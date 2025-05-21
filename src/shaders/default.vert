#version 330 core

in vec2 vert;
in vec2 texCoord;

out vec2 pos;

void main() {
    pos = texCoord;
    gl_Position = vec4(vert, 0.0, 1);
}