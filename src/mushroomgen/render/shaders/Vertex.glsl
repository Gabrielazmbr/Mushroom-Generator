#version 410 core
// PBR Shaders based on:
// Macey, Jon. (n.d.). PyNGLDemos/PBR/SimplePBR [Source code]
// Available from: https://github.com/NCCA/PyNGLDemos/tree/main/PBR/SimplePBR
layout(location = 0) in vec3 inVert;
layout(location = 1) in vec3 inNormal;
layout(location = 2) in vec2 inUV;

out vec2 TexCoords;
out vec3 WorldPos;
out vec3 Normal;

uniform mat4 MVP; // Model ViewProjection matrix
uniform mat4 M; // Model matrix
uniform mat3 normalMatrix; // Normal matrix

void main()
{
    WorldPos = vec3(M * vec4(inVert, 1.0));
    Normal = normalize(normalMatrix * inNormal);
    TexCoords = inUV;
    gl_Position = MVP * vec4(inVert, 1.0);
}
