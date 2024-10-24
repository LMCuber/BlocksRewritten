#version 330 core

uniform sampler2D tex;
uniform float time;
uniform vec2 windowSize;

in vec2 pos;

out vec4 fColor;

void main() {
    // init
    time;
    vec4 cur = texture(tex, pos);
    vec3 color = vec3(pos.y, pos.x, 1);
    fColor = vec4(color, 1.0); // texture() gives texture color at given UV (u, v) position. (r, g, b), a=1.0 so vec4
}