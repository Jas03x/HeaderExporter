
struct Vertex
{
    float position[3];
    float normal[3];
    float uv[2];
    uint16_t node_index;
};

enum { MAX_VERTICES_PER_POLYGON = 4 };
enum { MAX_STRING_LENGTH = 64 };

struct Polygon
{
    uint16_t start_index;
    uint8_t index_count;
};

struct Node
{
    char name[MAX_STRING_LENGTH];
    uint16_t parent_index;
    float matrix[16];
};

struct Mesh
{
    Vertex* vertex_array;
    uint16_t vertex_count;

    uint16_t* index_array;
    uint8_t index_count;

    const Polygon* polygon_array;
    uint32_t polygon_count;
};
