from typing import Dict, List, Any, Tuple
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
    """Calculate properties for a shell or surface shape."""
    if not shell:
        raise ValueError("Invalid shell shape: None")
    
    props = GProp_GProps()
    try:
        brepgprop_SurfaceProperties(shell, props)
    except Exception as e:
        raise ValueError(f"Failed to calculate surface properties: {str(e)}")
    
    # Topology checks first
    num_faces = count_subshapes(shell, TopAbs_FACE)
    num_edges = count_subshapes(shell, TopAbs_EDGE)
    num_vertices = count_subshapes(shell, TopAbs_VERTEX)
    
    # Basic validity checks
    if num_edges == 0 or num_vertices == 0:
        raise ValueError("Invalid geometry: Shell/surface has no edges or vertices")
    
    # Bounding box with tolerance
    bbox = Bnd_Box()
    brepbndlib.Add(shell, bbox, 1e-7)  # Added precision parameter
    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
    dimensions = (xmax - xmin, ymax - ymin, zmax - zmin)
    
    # Check for degenerate dimensions
    if any(abs(d) < 1e-6 for d in dimensions):
        raise ValueError("Invalid geometry: Shell/surface has zero dimension")
    
    try:
        surface_area = float(props.Mass())
        if surface_area < 1e-6:
            raise ValueError("Invalid geometry: Shell/surface has zero area")
        
        com = props.CentreOfMass()
        # Get principal properties with error checking
        principal_props = props.MatrixOfInertia()
        principal_moments = (
            round(float(principal_props.Value(1, 1)), 3),
            round(float(principal_props.Value(2, 2)), 3),
            round(float(principal_props.Value(3, 3)), 3)
        )
    except Exception as e:
        raise ValueError(f"Error calculating geometric properties: {str(e)}")
    
    return {
        "surface_area": round(surface_area, 3),
        "center_of_mass": (
            round(float(com.X()), 3),
            round(float(com.Y()), 3),
            round(float(com.Z()), 3)
        ),
        "dimensions": tuple(round(float(d), 3) for d in dimensions),
        "topology": {
            "faces": num_faces,
            "edges": num_edges,
            "vertices": num_vertices
        },
        "type": "shell" if num_faces > 1 else "surface",
        "principal_moments": principal_moments
    }

def get_face_properties(face: TopoDS_Shape):
    """Calculate properties specifically for a single face."""
    if not face:
        raise ValueError("Invalid face shape: None")
    
    props = GProp_GProps()
    try:
        brepgprop_SurfaceProperties(face, props)
    except Exception as e:
        raise ValueError(f"Failed to calculate face properties: {str(e)}")
    
    # Face-specific topology
    num_edges = count_subshapes(face, TopAbs_EDGE)
    num_vertices = count_subshapes(face, TopAbs_VERTEX)
    
    # Validity checks
    if num_edges < 3:
        raise ValueError("Invalid face geometry: Less than 3 edges")
    if num_vertices < 3:
        raise ValueError("Invalid face geometry: Less than 3 vertices")
    
    # Bounding box with tolerance
    bbox = Bnd_Box()
    brepbndlib.Add(face, bbox, 1e-7)
    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
    dimensions = (xmax - xmin, ymax - ymin, zmax - zmin)
    
    # Check for degenerate dimensions
    if sum(1 for d in dimensions if abs(d) < 1e-6) > 1:
        raise ValueError("Invalid face geometry: More than one zero dimension")
    
    try:
        area = float(props.Mass())
        if area < 1e-6:
            raise ValueError("Invalid face geometry: Zero area")
        
        com = props.CentreOfMass()
        
    except Exception as e:
        raise ValueError(f"Error calculating face properties: {str(e)}")
    
    return {
        "surface_area": round(area, 3),
        "center_of_mass": (
            round(float(com.X()), 3),
            round(float(com.Y()), 3),
            round(float(com.Z()), 3)
        ),
        "dimensions": tuple(round(float(d), 3) for d in dimensions),
        "topology": {
            "faces": 1,
            "edges": num_edges,
            "vertices": num_vertices
        },
        "type": "surface",
        "principal_moments": (
            round(float(area), 3),  # For a face, we use the area as the primary moment
            round(float(area), 3),
            round(float(area), 3)
        )
    }

def get_shape_properties(shape: TopoDS_Shape):
    """Global properties for models (solids, shells, or surfaces) with enhanced type detection."""
    if not shape:
        raise ValueError("Invalid shape: None")
    
    try:
        # First analyze what kind of shape we have
        num_solids = count_subshapes(shape, TopAbs_SOLID)
        num_shells = count_subshapes(shape, TopAbs_SHELL)
        num_faces = count_subshapes(shape, TopAbs_FACE)
        
        # Try to get solids first
        solids = get_solids_from_shape(shape)
        if solids:
            try:
                return get_solid_properties(solids[0])
            except Exception as e:
                # Log the error but continue trying other types
                pass
        
        # Try shells if no valid solids
        shells = get_shells_from_shape(shape)
        if shells:
            try:
                return get_shell_properties(shells[0])
            except Exception as e:
                # Log the error but continue trying faces
                pass
        
        # Finally try individual faces
        faces = get_faces_from_shape(shape)
        if faces:
            try:
                return get_face_properties(faces[0])
            except Exception as e:
                # If we get here, we've tried everything
                pass
        
        # If we get here, we couldn't process any geometry
        details = f"Found {num_solids} solids, {num_shells} shells, {num_faces} faces"
        if num_solids == 0 and num_shells == 0 and num_faces == 0:
            raise ValueError(f"No valid geometry found in shape. {details}")
        else:
            raise ValueError(f"Found geometry but failed to process it. {details}")
            
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

        # Volume or Surface Area with type-specific comparisons
        if "volume" in sub_props and "volume" in ref_props:
            # For solids
            measure_ok = abs(sub_props["volume"] - ref_props["volume"]) <= tol * max(abs(ref_props["volume"]), 1)
            measure_score = 100 - min(100, 100 * abs(sub_props["volume"] - ref_props["volume"]) /
                                  (abs(ref_props["volume"]) if abs(ref_props["volume"]) > 1e-6 else 1))
            feedback["volume"] = {"ok": measure_ok, "score": measure_score}
            score += measure_score
            total += 1
            
        else:
            # For shells and surfaces
            if "type" not in sub_props or "type" not in ref_props:
                raise ValueError("Missing shape type information")
                
            # Check if types match
            type_match = sub_props["type"] == ref_props["type"]
            type_score = 100 if type_match else 0
            feedback["type_match"] = {"ok": type_match, "score": type_score}
            score += type_score
            total += 1
            
            # Surface area comparison
            area_ok = abs(sub_props["surface_area"] - ref_props["surface_area"]) <= tol * max(abs(ref_props["surface_area"]), 1)
            area_score = 100 - min(100, 100 * abs(sub_props["surface_area"] - ref_props["surface_area"]) /
                                (abs(ref_props["surface_area"]) if abs(ref_props["surface_area"]) > 1e-6 else 1))
            
            # Topology comparison with weighted scoring
            edge_diff = abs(sub_props["topology"]["edges"] - ref_props["topology"]["edges"])
            vertex_diff = abs(sub_props["topology"]["vertices"] - ref_props["topology"]["vertices"])
            topo_score = 100
            if edge_diff > 0:
                topo_score -= min(50, edge_diff * 10)  # Deduct up to 50 points for edge differences
            if vertex_diff > 0:
                topo_score -= min(50, vertex_diff * 10)  # Deduct up to 50 points for vertex differences
            
            feedback["surface_analysis"] = {
                "area": {"ok": area_ok, "score": area_score},
                "topology": {"ok": edge_diff == 0 and vertex_diff == 0, "score": topo_score},
                "type": sub_props["type"],
                "details": {
                    "edge_difference": edge_diff,
                    "vertex_difference": vertex_diff
                }
            }
            
            # Add weighted scores to total
            score += area_score * 0.6  # Surface area is 60% of the score
            score += topo_score * 0.4  # Topology is 40% of the score
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
