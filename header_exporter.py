
import bpy
from bpy.props import (BoolProperty, FloatProperty, StringProperty, EnumProperty)
from bpy_extras.io_utils import (ImportHelper, ExportHelper, orientation_helper, path_reference_mode, axis_conversion)
from mathutils import Matrix

import os
import struct

bl_info = {
    "name": "Header Exporter",
    "author": "Jas",
    "version": (0, 0, 1),
    "blender": (4, 1, 1),
    "location": "File > Import-Export",
    "description": "Header Exporter",
    "warning": "",
    "support": "COMMUNITY",
    "category": "Import-Export"
}

class Vertex:
    def __init__(self, p, n, uv, node_index):
        self.position = tuple(p)
        self.normal = tuple(n)
        self.uv = tuple(uv)
        self.node_index = node_index
        self.hash_value = 0
    
    def finalize(self):
        self.hash_value = hash((self.position, self.normal, self.uv, self.node_index))

    def __eq__(self, other):
        return (self.position == other.position) and (self.normal == other.normal) and (self.uv == other.uv) and (self.node_index == other.node_index)

    def __hash__(self):
        return self.hash_value

class Polygon:
    def __init__(self):
        self.index_count = 0
        self.index_array = []

class Node:
    def __init__(self, name, parent, transform):
        self.name = name
        self.parent = parent
        self.transform = transform

class Bone:
    def __init__(self, name, offset_matrix):
        self.name = name
        self.offset_matrix = offset_matrix

class Index:
    def __init__(self):
        self.map = {}
        self.array = []

    def add(self, key, value):
        if self.map.get(key) != None:
            raise Exception("item {} already exists in index".format(key))
        self.map[key] = len(self.array)
        self.array.append(value)

    def get(self, key):
        return self.array[self.find(key)]
    
    def find(self, key):
        index = self.map.get(key, -1)
        if index == -1:
            raise Exception("item {} does not exist in index".format(key))
        return index
    
class Mesh:
    def __init__(self, name):
        self.name = name
        self.vertex_set = []
        self.vertex_map = {}
        self.polygon_array = []

class Object:
    def __init__(self, name, mesh_index):
        self.name = name
        self.mesh_index = mesh_index

class Scene:
    def __init__(self):
        self.mesh_array = []
        self.object_array = []
        self.bone_index = Index()
        self.node_index = Index()
        self.texture_array = []

class Header_Exporter(bpy.types.Operator, ExportHelper):
    bl_idname = "export_scene.header"
    bl_label = "Export Header"

    filename_ext = ".h"

    def write_file(self, data):
        f = open(self.filepath, "w")
        f.write(struct.pack("=IIIIIIII", MDL_SIG, 1, 0, 0, 0, 0, 0, 0))
        self.write_node_block(f, data.node_index.array)
        self.write_bone_block(f, data.bone_index.array)
        self.write_material_block(f, data.ambient_texture, data.diffuse_texture, data.specular_texture)
        self.write_mesh_block(f, data.mesh_array)
        f.write(struct.pack("=I", MDL_EOF))
        f.close()

    def process(self):
        scene = Scene()

        mesh_map = {}

        for mesh in bpy.data.meshes:
            uv_array = mesh.uv_layers.active.uv

            mesh = Mesh(mesh.name)
            node_index = scene.node_index.find(mesh.name)
            for p in mesh.polygons:
                if p.loop_total != 3 and p.loop_total != 4:
                    raise Exception("mesh has unsupported polygons (count={})".format(p.loop_total))

                polygon = Polygon()
                for i in range(p.loop_start, p.loop_start + p.loop_total):
                    n = mesh.loops[i].normal
                    v = mesh.vertices[mesh.loops[i].vertex_index]
                    vertex = None

                    vertex = MDL_Vertex(v.co, n, uv_array[i].uv, node_index)
                    vertex.finalize()

                    index = mesh.vertex_map.get(vertex, -1)
                    if index == -1:
                        index = len(mesh.vertex_set)
                        mesh.vertex_map[vertex] = index
                        mesh.vertex_set.append(vertex)
                    polygon.index_count += 1
                    polygon.index_array.append(index)
                mesh.polygon_array.append(polygon)
            
            mesh_map[mesh.name] = len(scene.mesh_array)
            scene.mesh_array.append(mesh)
        
        for _object in bpy.data.objects:
            parent = None if _object.parent is None else _object.parent.name
            scene.node_index.add(_object.name, Node(_object.name, parent, _object.matrix_local.transposed()))
            scene.object_array.add(Object(_object.name, mesh_map[_object.name]))

        return scene

    def execute(self, context):
        try:
            mdl = self.process()
            self.write_file(mdl)
        except Exception as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
        return {"FINISHED"}

def menu_func_export(self, context):
    self.layout.operator(Header_Exporter.bl_idname, text="Header (.h)")

def register():
    bpy.utils.register_class(Header_Exporter)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(Header_Exporter)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()
