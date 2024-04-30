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