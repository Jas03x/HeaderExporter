
import bpy
from bpy.props import (BoolProperty, FloatProperty, StringProperty, EnumProperty)
from bpy_extras.io_utils import (ImportHelper, ExportHelper, orientation_helper, path_reference_mode, axis_conversion)
from mathutils import Matrix

import os

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

definitions = \
"""
#ifndef HEADER_DEFINITIONS
#define HEADER_DEFINITIONS
enum { MAX_VERTICES_PER_POLYGON = 4 };
enum { MAX_STRING_LENGTH = 64 };

struct Vertex
{
    float position[3];
    float normal[3];
    float uv[2];
};

struct Polygon
{
    uint16_t indices[MAX_VERTICES_PER_POLYGON];
    uint8_t index_count;
};

struct Texture
{
    char name[MAX_STRING_LENGTH];

    uint32_t width;
    uint32_t height;
    uint8_t* pixels;
};

struct Mesh
{
    char name[MAX_STRING_LENGTH];

    Vertex* vertex_array;
    uint16_t vertex_count;

    const Polygon* polygon_array;
    uint32_t polygon_count;
};

struct Node
{
    char name[MAX_STRING_LENGTH];
    float matrix[16];
    uint16_t parent_index;
    uint16_t mesh_index;
};

struct Scene
{
    Mesh* mesh_array;
    uint16_t mesh_count;

    Node* node_array;
    uint16_t node_count;

    Texture texture_array;
    uint8_t texture_count;
};
#endif // HEADER_DEFINITIONS
"""

class Vertex:
    def __init__(self, p, n, uv):
        self.position = tuple(p)
        self.normal = tuple(n)
        self.uv = tuple(uv)
        self.hash_value = 0
    
    def finalize(self):
        self.hash_value = hash((self.position, self.normal, self.uv))

    def __eq__(self, other):
        return (self.position == other.position) and (self.normal == other.normal) and (self.uv == other.uv)

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
    
class Mesh:
    def __init__(self, name):
        self.name = name
        self.vertex_set = []
        self.vertex_map = {}
        self.polygon_array = []

class Node:
    def __init__(self, name, parent, mesh_index, matrix):
        self.name = name
        self.mesh_index = mesh_index
        self.parent = parent
        self.matrix = matrix

class Scene:
    def __init__(self):
        self.mesh_array = []
        self.node_array = []
        self.texture_array = []

class Header_Exporter(bpy.types.Operator, ExportHelper):
    bl_idname = "export_scene.header"
    bl_label = "Export Header"

    filename_ext = ".h"

    def write_file(self, scene):
        f = open(self.filepath, "w")
        f.write("#ifndef {}_H\n".format(os.path.basename(self.filepath).upper().replace(".H", "")))
        f.write("{}\n".format(definitions))
        for mesh in scene.mesh_array:
            vertex_string = "Vertex {}_VERTICES[] = \n{{\n".format(mesh.name.upper())
            for vertex in mesh.vertex_set:
                vertex_string += "\t{{ {{ {}, {}, {} }}, {{ {}, {}, {} }}, {{ {}, {} }} }},\n".format(
                    vertex.position[0], vertex.position[1], vertex.position[2],
                    vertex.normal[0], vertex.normal[1], vertex.normal[2],
                    vertex.uv[0], vertex.uv[1]
                )
            vertex_string += "};\n\n"
            f.write(vertex_string)
        for mesh in scene.mesh_array:
            polygon_string = "Polygon {}_POLYGONS[] = \n{{\n".format(mesh.name.upper())
            for polygon in mesh.polygon_array:
                polygon_string += "\t"
                if polygon.index_count == 3:
                    polygon_string += "{{ {{ {}, {}, {}, 0 }}, 3 }},\n".format(polygon.index_array[0], polygon.index_array[1], polygon.index_array[2])
                elif polygon.index_count == 4:
                    polygon_string += "{{ {{ {}, {}, {}, {} }}, 4 }},\n".format(polygon.index_array[0], polygon.index_array[1], polygon.index_array[2], polygon.index_array[3])
                else:
                    raise Exception("unexpected polygon index count {}".format(polygon.index_count))
            polygon_string += "};\n\n"
            f.write(polygon_string)
        for mesh in scene.mesh_array:
            mesh_string = "Mesh {} = \n{{\n".format(mesh.name.upper())
            mesh_string += "\t\"{}\",\n".format(mesh.name)
            mesh_string += "\t{}_VERTICES, sizeof({}_VERTICES),\n".format(mesh.name.upper(), mesh.name.upper())
            mesh_string += "\t{}_POLYGONS, sizeof({}_POLYGONS)\n".format(mesh.name.upper(), mesh.name.upper())
            mesh_string += "};\n\n"
            f.write(mesh_string)

        mesh_array_string = "Mesh MESHES[] = \n{\n"
        for mesh in scene.mesh_array:
            mesh_array_string += "\t{},\n".format(mesh.name.upper())
        mesh_array_string += "};\n\n"
        f.write(mesh_array_string)

        node_string = "Node NODES[] = \n{\n"
        for node in scene.node_array:
            node_string += "\t{{ {}, {{ {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {} }}, {}, {} }}\n".format(
                node.name,
                node.matrix[0][0], node.matrix[0][1], node.matrix[0][2], node.matrix[0][3],
                node.matrix[1][0], node.matrix[1][1], node.matrix[1][2], node.matrix[1][3],
                node.matrix[2][0], node.matrix[2][1], node.matrix[2][2], node.matrix[2][3],
                node.matrix[3][0], node.matrix[3][1], node.matrix[3][2], node.matrix[3][3],
                node.parent,
                node.mesh_index
            )
        node_string += "};\n\n"
        f.write(node_string)

        f.write("#endif")
        f.close()

    def process(self):
        scene = Scene()

        mesh_map = {}
        node_map = {}

        for texture in bpy.data.images:
            scene.texture_array.append(texture.filepath)

        for mesh in bpy.data.meshes:
            uv_array = mesh.uv_layers.active.uv

            mesh_data = Mesh(mesh.name)
            for p in mesh.polygons:
                if p.loop_total != 3 and p.loop_total != 4:
                    raise Exception("mesh has unsupported polygons (count={})".format(p.loop_total))

                polygon = Polygon()
                for i in range(p.loop_start, p.loop_start + p.loop_total):
                    n = mesh.loops[i].normal
                    v = mesh.vertices[mesh.loops[i].vertex_index]
                    vertex = None

                    vertex = Vertex(v.co, n, uv_array[i].vector)
                    vertex.finalize()

                    index = mesh_data.vertex_map.get(vertex, -1)
                    if index == -1:
                        index = len(mesh_data.vertex_set)
                        mesh_data.vertex_map[vertex] = index
                        mesh_data.vertex_set.append(vertex)
                    polygon.index_count += 1
                    polygon.index_array.append(index)
                mesh_data.polygon_array.append(polygon)
            
            mesh_map[mesh.name] = len(scene.mesh_array)
            scene.mesh_array.append(mesh_data)
        
        for node in bpy.data.objects:
            parent = None if node.parent is None else node.parent.name
            node_map[node.name] = len(scene.node_array)
            scene.node_array.append(Node(node.name, node_map[node.parent.name] if node.parent != None else -1, mesh_map.get(node.name, -1), node.matrix_local.transposed()))

        return scene

    def execute(self, context):
        try:
            scene = self.process()
            self.write_file(scene)
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
