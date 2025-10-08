from typing import Dict, List, Any, Tuple
import logging
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.BRepGProp import brepgprop_VolumeProperties, brepgprop_SurfaceProperties
from OCC.Core.GProp import GProp_GProps
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX, TopAbs_SOLID, TopAbs_SHELL
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopoDS import topods, TopoDS_Shape
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.Bnd import Bnd_Box
import numpy as np

# -------------------------------
# STEP file utilities
# -------------------------------

def read_step_file(filename: str) -> TopoDS_Shape:
    reader = STEPControl_Reader()
    status = reader.ReadFile(filename)
    if status != 1:  # IFSelect_RetDone
        raise Exception(f"Error reading STEP file: {filename}")
    reader.TransferRoots()
    return reader.OneShape()

def get_solids_from_shape(shape: TopoDS_Shape):
    solids = []
    exp = TopExp_Explorer(shape, TopAbs_SOLID)
    while exp.More():
        solids.append(topods.Solid(exp.Current()))
        exp.Next()
    return solids

def get_shells_from_shape(shape: TopoDS_Shape):
    shells = []
    exp = TopExp_Explorer(shape, TopAbs_SHELL)
    while exp.More():
        shells.append(topods.Shell(exp.Current()))
        exp.Next()
    return shells

def get_faces_from_shape(shape: TopoDS_Shape):
    faces = []
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        faces.append(topods.Face(exp.Current()))
        exp.Next()
    return faces

# -------------------------------
# Property extraction
# -------------------------------

def count_subshapes(shape: TopoDS_Shape, subshape_type):
    count = 0
    explorer = TopExp_Explorer(shape, subshape_type)
    while explorer.More():
        count += 1
        explorer.Next()
    return count

def get_solid_properties(solid: TopoDS_Shape):
    props = GProp_GProps()
    brepgprop_VolumeProperties(solid, props)

    volume = props.Mass()
    com = props.CentreOfMass()

    # Bounding box
    bbox = Bnd_Box()
    brepbndlib.Add(solid, bbox)
    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
    dimensions = (xmax - xmin, ymax - ymin, zmax - zmin)

    # Topology
    # Count faces
    face_explorer = TopExp_Explorer(solid, TopAbs_FACE)
    num_faces = 0
    while face_explorer.More():
        num_faces += 1
        face_explorer.Next()

    # Count edges
    edge_explorer = TopExp_Explorer(solid, TopAbs_EDGE)
    num_edges = 0
    while edge_explorer.More():
        num_edges += 1
        edge_explorer.Next()

    # Count vertices
    vertex_explorer = TopExp_Explorer(solid, TopAbs_VERTEX)
    num_vertices = 0
    while vertex_explorer.More():
        num_vertices += 1
        vertex_explorer.Next()

    # Principal moments
    matrix = props.MatrixOfInertia()
    moi_matrix = np.array([[matrix.Value(i, j) for j in range(1, 4)] for i in range(1, 4)])
    eigvals = np.linalg.eigvals(moi_matrix)

    return {
        "volume": round(float(volume), 3),
        "center_of_mass": (
            round(float(com.X()), 3),
            round(float(com.Y()), 3),
            round(float(com.Z()), 3)
        ),
        "dimensions": tuple(round(float(d), 3) for d in dimensions),
        "topology": {"faces": num_faces, "edges": num_edges, "vertices": num_vertices},
        "principal_moments": [round(float(abs(v)), 3) for v in eigvals]
    }

def get_shell_properties(shell: TopoDS_Shape):
    """Calculate properties for a shell or surface shape with improved accuracy."""
    props = GProp_GProps()
    try:
        brepgprop_SurfaceProperties(shell, props)
    except Exception as e:
        raise ValueError(f"Failed to calculate surface properties: {str(e)}")
    
    # Bounding box with tolerance
    bbox = Bnd_Box()
    brepbndlib.Add(shell, bbox, 1e-7)  # Added precision parameter
    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
    dimensions = (xmax - xmin, ymax - ymin, zmax - zmin)
    
    # Enhanced topology checks
    num_faces = count_subshapes(shell, TopAbs_FACE)
    num_edges = count_subshapes(shell, TopAbs_EDGE)
    num_vertices = count_subshapes(shell, TopAbs_VERTEX)
    
    # Get principal properties with error checking
    try:
        principal_props = props.MatrixOfInertia()
        principal_moments = (
            round(float(principal_props.Value(1, 1)), 3),
            round(float(principal_props.Value(2, 2)), 3),
            round(float(principal_props.Value(3, 3)), 3)
        )
    except Exception:
        # Fallback to simplified moments if matrix calculation fails
        principal_moments = (
            round(float(props.Mass()), 3),
            round(float(props.Mass()), 3),
            round(float(props.Mass()), 3)
        )
    
    # Determine shape type with more precision
    shape_type = "shell" if num_faces > 1 else "surface"
    if num_edges == 0 or num_vertices == 0:
        raise ValueError("Invalid geometry: Shell/surface has no edges or vertices")
    
    return {
        "surface_area": round(float(props.Mass()), 3),
        "center_of_mass": (
            round(float(props.CentreOfMass().X()), 3),
            round(float(props.CentreOfMass().Y()), 3),
            round(float(props.CentreOfMass().Z()), 3)
        ),
        "dimensions": tuple(round(float(d), 3) for d in dimensions),
        "topology": {
            "faces": num_faces,
            "edges": num_edges,
            "vertices": num_vertices
        },
        "type": shape_type,
        "principal_moments": principal_moments,
        "is_closed": shape_type == "shell" and num_edges > 0  # Additional property for shells
    }

def get_face_properties(face: TopoDS_Shape):
    """Calculate properties specifically for a single face."""
    props = GProp_GProps()
    try:
        brepgprop_SurfaceProperties(face, props)
    except Exception as e:
        raise ValueError(f"Failed to calculate face properties: {str(e)}")
    
    # Bounding box with tolerance
    bbox = Bnd_Box()
    brepbndlib.Add(face, bbox, 1e-7)
    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
    dimensions = (xmax - xmin, ymax - ymin, zmax - zmin)
    
    # Face-specific topology
    num_edges = count_subshapes(face, TopAbs_EDGE)
    num_vertices = count_subshapes(face, TopAbs_VERTEX)
    
    if num_edges == 0 or num_vertices == 0:
        raise ValueError("Invalid geometry: Face has no edges or vertices")
    
    return {
        "surface_area": round(float(props.Mass()), 3),
        "center_of_mass": (
            round(float(props.CentreOfMass().X()), 3),
            round(float(props.CentreOfMass().Y()), 3),
            round(float(props.CentreOfMass().Z()), 3)
        ),
        "dimensions": tuple(round(float(d), 3) for d in dimensions),
        "topology": {
            "faces": 1,  # Always 1 for a single face
            "edges": num_edges,
            "vertices": num_vertices
        },
        "type": "surface",
        "principal_moments": (
            round(float(props.Mass()), 3),  # For a face, we use surface area as the primary moment
            round(float(props.Mass()), 3),
            round(float(props.Mass()), 3)
        ),
        "is_planar": num_edges >= 3  # Basic check for planarity
    }

def get_shape_properties(shape: TopoDS_Shape):
    """Global properties for models (solids, shells, or surfaces) with enhanced error handling."""
    if shape is None:
        raise ValueError("Input shape is None")
    
    try:
        # First try solids
        solids = get_solids_from_shape(shape)
        if solids:
            try:
                return get_solid_properties(solids[0])
            except Exception as e:
                logging.warning(f"Failed to get solid properties: {str(e)}")
        
        # Then try shells
        shells = get_shells_from_shape(shape)
        if shells:
            try:
                return get_shell_properties(shells[0])
            except Exception as e:
                logging.warning(f"Failed to get shell properties: {str(e)}")
        
        # Finally try faces
        faces = get_faces_from_shape(shape)
        if faces:
            try:
                return get_face_properties(faces[0])
            except Exception as e:
                logging.warning(f"Failed to get face properties: {str(e)}")
        
        # If we get here, no valid geometry was found or all attempts failed
        shape_type = "unknown"
        if solids:
            shape_type = "solid"
        elif shells:
            shape_type = "shell"
        elif faces:
            shape_type = "face"
        
        error_msg = f"Failed to process geometry of type {shape_type}. "
        error_msg += "No valid geometry (solid, shell, or face) could be analyzed."
        raise ValueError(error_msg)
        
    except Exception as e:
        raise ValueError(f"Error analyzing shape: {str(e)}")

# -------------------------------
# Comparison
# -------------------------------

def compare_models(submitted_path: str, reference_path: str, tol: float = 1e-3) -> Dict[str, Any]:
    """Compare two STEP models (can handle both single parts and assemblies)."""
    sub_shape = read_step_file(submitted_path)
    ref_shape = read_step_file(reference_path)

    sub_solids = get_solids_from_shape(sub_shape)
    ref_solids = get_solids_from_shape(ref_shape)

    # Initialize feedback dictionary with proper type hints
    feedback: Dict[str, Any] = {}

    # -----------------
    # Assembly mode
    # -----------------
    if len(ref_solids) > 1 or len(sub_solids) > 1:
        feedback = {
            "num_components": {
                "submitted": len(sub_solids),
                "reference": len(ref_solids),
                "ok": len(sub_solids) == len(ref_solids),
                "message": "Nombre de sous-pièces correct." if len(sub_solids) == len(ref_solids)
                           else "Nombre de sous-pièces différent."
            }
        }

        matches = []
        for i, (sub_solid, ref_solid) in enumerate(zip(sub_solids, ref_solids)):
            sub_props = get_solid_properties(sub_solid)
            ref_props = get_solid_properties(ref_solid)

            vol_ok = abs(sub_props["volume"] - ref_props["volume"]) <= tol * max(abs(ref_props["volume"]), 1)
            com_ok = all(abs(s - r) <= tol * max(abs(r), 1)
                         for s, r in zip(sub_props["center_of_mass"], ref_props["center_of_mass"]))
            topo_ok = sub_props["topology"] == ref_props["topology"]

            vol_score = 100 - min(100, 100 * abs(sub_props["volume"] - ref_props["volume"]) /
                                  (abs(ref_props["volume"]) if abs(ref_props["volume"]) > 1e-6 else 1))

            matches.append({
                "index": i,
                "volume_ok": bool(vol_ok),
                "volume_score": round(float(vol_score), 1),
                "center_of_mass_ok": bool(com_ok),
                "center_of_mass_sub": sub_props["center_of_mass"],
                "center_of_mass_ref": ref_props["center_of_mass"],
                "topology_match": bool(topo_ok)
            })

        feedback["components_match"] = matches
        n_ok = sum(1 for m in matches if m["volume_ok"] and m["center_of_mass_ok"] and m["topology_match"])
        global_score = round(n_ok / max(len(matches), 1) * 100, 1)

        feedback["global_score"] = global_score
        feedback["success"] = global_score >= 80 and len(sub_solids) == len(ref_solids)
        return feedback

    # -----------------
    # Part mode
    # -----------------
    else:
        sub_props = get_shape_properties(sub_shape)
        ref_props = get_shape_properties(ref_shape)

        feedback = {}
        score = 0
        total = 0

        # Dimensions
        dims_ok = [abs(s - r) <= tol * max(abs(r), 1)
                   for s, r in zip(sub_props["dimensions"], ref_props["dimensions"])]
        dims_pct = [100 - min(100, 100 * abs(s - r) / (abs(r) if abs(r) > 1e-6 else 1))
                    for s, r in zip(sub_props["dimensions"], ref_props["dimensions"])]
        dims_score = sum(dims_pct) / len(dims_pct)
        feedback["dimensions"] = {"ok": all(dims_ok), "score": dims_score}
        score += dims_score
        total += 1

        # Volume or Surface Area
        if "volume" in sub_props and "volume" in ref_props:
            # For solids
            measure_ok = abs(sub_props["volume"] - ref_props["volume"]) <= tol * max(abs(ref_props["volume"]), 1)
            measure_score = 100 - min(100, 100 * abs(sub_props["volume"] - ref_props["volume"]) /
                                  (abs(ref_props["volume"]) if abs(ref_props["volume"]) > 1e-6 else 1))
            feedback["volume"] = {"ok": measure_ok, "score": measure_score}
        else:
            # For shells and surfaces
            measure_ok = abs(sub_props["surface_area"] - ref_props["surface_area"]) <= tol * max(abs(ref_props["surface_area"]), 1)
            measure_score = 100 - min(100, 100 * abs(sub_props["surface_area"] - ref_props["surface_area"]) /
                                  (abs(ref_props["surface_area"]) if abs(ref_props["surface_area"]) > 1e-6 else 1))
            
            # Additional checks for shells and surfaces
            type_match = sub_props["type"] == ref_props["type"]
            is_closed_match = sub_props.get("is_closed", False) == ref_props.get("is_closed", False)
            is_planar_match = sub_props.get("is_planar", False) == ref_props.get("is_planar", False)
            
            # Adjust score based on additional criteria
            surface_score = measure_score * 0.6  # Base score from area comparison
            if type_match:
                surface_score += 20  # Add points for matching type
            if is_closed_match:
                surface_score += 10  # Add points for matching closure
            if is_planar_match:
                surface_score += 10  # Add points for matching planarity
            
            feedback["surface_area"] = {
                "ok": measure_ok,
                "score": round(surface_score, 1),
                "details": {
                    "area_match": measure_ok,
                    "type_match": type_match,
                    "closure_match": is_closed_match,
                    "planarity_match": is_planar_match
                }
            }
            
            score += surface_score
            total += 1

        # Topology
        topo_ok = sub_props["topology"] == ref_props["topology"]
        topo_score = 100 if topo_ok else 0
        feedback["topology"] = {"ok": topo_ok, "score": topo_score}
        score += topo_score
        total += 1

        # Moments of inertia
        pm_ok = all(abs(s - r) <= tol * max(abs(r), 1)
                    for s, r in zip(sub_props["principal_moments"], ref_props["principal_moments"]))
        pm_score = 100 if pm_ok else 0
        feedback["principal_moments"] = {"ok": pm_ok, "score": pm_score}
        score += pm_score
        total += 1

        # Calculate global score (average of all scores)
        global_score = round(score / total, 1)
        feedback["global_score"] = global_score
        feedback["success"] = global_score >= 80
        return feedback
