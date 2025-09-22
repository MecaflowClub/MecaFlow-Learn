from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.BRepGProp import brepgprop_VolumeProperties, brepgprop_LinearProperties
from OCC.Core.GProp import GProp_GProps
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_EDGE, TopAbs_VERTEX, TopAbs_SOLID, TopAbs_COMPOUND, TopAbs_SHELL
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopoDS import topods, TopoDS_Iterator, TopoDS_Shape
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.Bnd import Bnd_Box
from typing import Dict, List, Tuple, Union, Any
import numpy as np

def read_step_file(filename: str) -> TopoDS_Shape:
    """Read a STEP file and return the shape"""
    reader = STEPControl_Reader()
    status = reader.ReadFile(filename)
    if status != 1:  # IFSelect_RetDone value is 1
        raise Exception(f"Error reading STEP file: {filename}")
    
    reader.TransferRoots()
    return reader.OneShape()

def get_solids_from_shape(shape):
    """Extract all solids from a shape (handles both single parts and assemblies)"""
    solids = []
    
    # First check if it's directly a solid
    solid_explorer = TopExp_Explorer(shape, TopAbs_SOLID)
    while solid_explorer.More():
        solids.append(topods.Solid(solid_explorer.Current()))
        solid_explorer.Next()
    
    return solids

def get_solid_properties(solid):
    """Get properties for a single solid"""
    props = GProp_GProps()
    brepgprop_VolumeProperties(solid, props)
    
    # Volume
    volume = props.Mass()
    
    # Center of mass
    com = props.CentreOfMass()
    center_of_mass = (com.X(), com.Y(), com.Z())
    
    # Bounding box
    bbox = Bnd_Box()
    brepbndlib.Add(solid, bbox)
    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
    dimensions = (xmax-xmin, ymax-ymin, zmax-zmin)
    
    # Topology
    face_explorer = TopExp_Explorer(solid, TopAbs_FACE)
    edge_explorer = TopExp_Explorer(solid, TopAbs_EDGE)
    vert_explorer = TopExp_Explorer(solid, TopAbs_VERTEX)
    
    topology = {
        "faces": sum(1 for _ in face_explorer),
        "edges": sum(1 for _ in edge_explorer),
        "vertices": sum(1 for _ in vert_explorer)
    }
    
    # Principal moments of inertia
    matrix = props.MatrixOfInertia()
    moi_matrix = np.array([
        [matrix.Value(i,j) for j in range(1,4)]
        for i in range(1,4)
    ])
    eigvals = np.linalg.eigvals(moi_matrix)
    principal_moments = [abs(v) for v in eigvals]
    
    return {
        "volume": round(volume, 3),
        "center_of_mass": tuple(round(x, 3) for x in center_of_mass),
        "dimensions": tuple(round(d, 3) for d in dimensions),
        "topology": topology,
        "principal_moments": [round(m, 3) for m in principal_moments]
    }

def compare_models(submitted_path: str, reference_path: str, tol: float = 1e-3) -> Dict[str, Any]:
    """Compare two STEP models (can handle both single parts and assemblies)"""
    try:
        # Read files
        sub_shape = read_step_file(submitted_path)
        ref_shape = read_step_file(reference_path)
        
        # Get solids
        sub_solids = get_solids_from_shape(sub_shape)
        ref_solids = get_solids_from_shape(ref_shape)
        
        # Basic comparison of number of solids
        feedback: Dict[str, Any] = {
            "num_components": {
                "submitted": len(sub_solids),
                "reference": len(ref_solids),
                "ok": len(sub_solids) == len(ref_solids),
                "message": "Nombre de sous-pièces correct." if len(sub_solids) == len(ref_solids) 
                          else "Nombre de sous-pièces différent."
            }
        }
        
        # Compare individual solids
        matches: List[Dict[str, Any]] = []
        for i, (sub_solid, ref_solid) in enumerate(zip(sub_solids, ref_solids)):
            sub_props = get_solid_properties(sub_solid)
            ref_props = get_solid_properties(ref_solid)
            
            # Check volume
            vol_ok = abs(sub_props["volume"] - ref_props["volume"]) <= tol * max(abs(ref_props["volume"]), 1)
            
            # Check center of mass
            com_ok = all(abs(s - r) <= tol * max(abs(r), 1) 
                        for s, r in zip(sub_props["center_of_mass"], ref_props["center_of_mass"]))
            
            # Calculate volume score
            vol_score = 100 - min(100, 100 * abs(sub_props["volume"] - ref_props["volume"]) / 
                                (abs(ref_props["volume"]) if abs(ref_props["volume"]) > 1e-6 else 1))
            
            matches.append({
                "index": i,
                "volume_ok": bool(vol_ok),
                "volume_score": round(vol_score, 1),
                "center_of_mass_ok": bool(com_ok),
                "center_of_mass_sub": sub_props["center_of_mass"],
                "center_of_mass_ref": ref_props["center_of_mass"],
                "topology_match": sub_props["topology"] == ref_props["topology"]
            })
        
        feedback["components_match"] = matches
        
        # Calculate global score
        n_ok = sum(1 for m in matches if m["volume_ok"] and m["center_of_mass_ok"] and m["topology_match"])
        global_score = round(n_ok / max(len(matches), 1) * 100, 1)
        
        feedback["global_score"] = global_score
        feedback["success"] = global_score >= 90 and len(sub_solids) == len(ref_solids)
        
        return feedback
        
    except (RuntimeError, ValueError, IOError) as e:
        return {
            "success": False,
            "error": str(e),
            "global_score": 0
        }
        pm_score = 100 if pm_ok else 0
        score += pm_score
        total += 100

        # Calculate global score
        global_score = score / total * 100

        return {
            "success": global_score >= 90,
            "score": round(global_score, 2),
            "feedback": {
                "dimensions": {"ok": all(dims_ok), "score": dims_score},
                "volume": {"ok": vol_ok, "score": vol_score},
                "topology": {"ok": topo_ok, "score": topo_score},
                "principal_moments": {"ok": pm_ok, "score": pm_score}
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }