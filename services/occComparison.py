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

def merge_shell_properties(shells_props):
    """Merge properties from multiple shells into a single property set."""
    if not shells_props:
        return None
    
    total_area = 0.0
    weighted_com = [0.0, 0.0, 0.0]
    total_edges = 0
    total_vertices = 0
    total_faces = 0
    
    # Find the overall bounding box
    min_coords = [float('inf'), float('inf'), float('inf')]
    max_coords = [float('-inf'), float('-inf'), float('-inf')]
    
    for prop in shells_props:
        area = prop["surface_area"]
        total_area += area
        
        # Weighted center of mass
        com = prop["center_of_mass"]
        for i in range(3):
            weighted_com[i] += com[i] * area
            
        # Update bounding box
        dims = prop["dimensions"]
        com = prop["center_of_mass"]
        for i in range(3):
            min_coords[i] = min(min_coords[i], com[i] - dims[i]/2)
            max_coords[i] = max(max_coords[i], com[i] + dims[i]/2)
        
        # Accumulate topology
        total_edges += prop["topology"]["edges"]
        total_vertices += prop["topology"]["vertices"]
        total_faces += prop["topology"]["faces"]
    
    # Finalize center of mass
    if total_area > 0:
        weighted_com = [x/total_area for x in weighted_com]
    
    # Calculate overall dimensions
    dimensions = [max_coords[i] - min_coords[i] for i in range(3)]
    
    return {
        "surface_area": round(total_area, 3),
        "center_of_mass": tuple(round(x, 3) for x in weighted_com),
        "dimensions": tuple(round(x, 3) for x in dimensions),
        "topology": {
            "faces": total_faces,
            "edges": total_edges,
            "vertices": total_vertices
        },
        "type": "multi-shell",
        "principal_moments": tuple(round(total_area, 3) for _ in range(3)),  # Simplified for multi-shell
        "num_shells": len(shells_props)
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
                pass
        
        # Handle shells - try to process all shells
        shells = get_shells_from_shape(shape)
        if shells:
            try:
                if len(shells) == 1:
                    return get_shell_properties(shells[0])
                else:
                    # Process multiple shells
                    shell_properties = []
                    for shell in shells:
                        try:
                            props = get_shell_properties(shell)
                            shell_properties.append(props)
                        except Exception:
                            continue
                    
                    if shell_properties:
                        return merge_shell_properties(shell_properties)
                    
            except Exception as e:
                pass
        
        # Finally try individual faces if no valid shells
        faces = get_faces_from_shape(shape)
        if faces:
            if len(faces) == 1:
                try:
                    return get_face_properties(faces[0])
                except Exception:
                    pass
            else:
                # Try to process all faces as a collection
                face_properties = []
                for face in faces:
                    try:
                        props = get_face_properties(face)
                        face_properties.append(props)
                    except Exception:
                        continue
                
                if face_properties:
                    return merge_shell_properties(face_properties)  # Reuse the merge function
        
        # If we get here, we couldn't process any geometry
        details = f"Found {num_solids} solids, {num_shells} shells, {num_faces} faces"
        if num_solids == 0 and num_shells == 0 and num_faces == 0:
            raise ValueError(f"No valid geometry found in shape. {details}")
        else:
            raise ValueError(f"Failed to process any valid geometry. {details}")
            
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

        if not sub_props or not ref_props:
            raise ValueError("Failed to get properties for comparison")

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
            # For shells and surfaces (including multi-shell)
            if "type" not in sub_props or "type" not in ref_props:
                raise ValueError("Missing shape type information")
            
            # Type comparison with more flexibility
            sub_type = sub_props["type"]
            ref_type = ref_props["type"]
            type_match = sub_type == ref_type or (
                sub_type in ["shell", "multi-shell"] and ref_type in ["shell", "multi-shell"]
            )
            type_score = 100 if type_match else 50 if (sub_type != "surface" and ref_type != "surface") else 0
            feedback["type_match"] = {
                "ok": type_match,
                "score": type_score,
                "submitted": sub_type,
                "reference": ref_type
            }
            score += type_score
            total += 1
            
            # Surface area comparison with tolerance based on complexity
            area_tolerance = tol * (2.0 if sub_type == "multi-shell" or ref_type == "multi-shell" else 1.0)
            area_ok = abs(sub_props["surface_area"] - ref_props["surface_area"]) <= area_tolerance * max(abs(ref_props["surface_area"]), 1)
            area_score = 100 - min(100, 100 * abs(sub_props["surface_area"] - ref_props["surface_area"]) /
                                (abs(ref_props["surface_area"]) if abs(ref_props["surface_area"]) > 1e-6 else 1))
            
            # Enhanced topology comparison for multi-shell
            sub_topo = sub_props["topology"]
            ref_topo = ref_props["topology"]
            
            # Calculate topology differences with tolerance for multi-shell
            edge_diff_pct = abs(sub_topo["edges"] - ref_topo["edges"]) / max(ref_topo["edges"], 1)
            vertex_diff_pct = abs(sub_topo["vertices"] - ref_topo["vertices"]) / max(ref_topo["vertices"], 1)
            face_diff_pct = abs(sub_topo["faces"] - ref_topo["faces"]) / max(ref_topo["faces"], 1)
            
            # More lenient scoring for multi-shell objects
            topo_tolerance = 0.2 if (sub_type == "multi-shell" or ref_type == "multi-shell") else 0.1
            topo_score = 100
            if edge_diff_pct > topo_tolerance:
                topo_score -= min(40, edge_diff_pct * 200)
            if vertex_diff_pct > topo_tolerance:
                topo_score -= min(30, vertex_diff_pct * 150)
            if face_diff_pct > topo_tolerance:
                topo_score -= min(30, face_diff_pct * 150)
            
            topo_score = max(0, topo_score)  # Ensure non-negative score
            
            feedback["surface_analysis"] = {
                "area": {"ok": area_ok, "score": round(area_score, 1)},
                "topology": {
                    "ok": topo_score > 80,
                    "score": round(topo_score, 1)
                },
                "type": sub_type,
                "details": {
                    "edge_difference_percent": round(edge_diff_pct * 100, 1),
                    "vertex_difference_percent": round(vertex_diff_pct * 100, 1),
                    "face_difference_percent": round(face_diff_pct * 100, 1),
                    "num_shells": sub_props.get("num_shells", 1)
                }
            }
            
            # Weighted scoring adjusted for multi-shell
            area_weight = 0.5 if (sub_type == "multi-shell" or ref_type == "multi-shell") else 0.6
            topo_weight = 1.0 - area_weight
            
            score += area_score * area_weight
            score += topo_score * topo_weight
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
