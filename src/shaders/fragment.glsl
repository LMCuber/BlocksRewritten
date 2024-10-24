#version 330 core

uniform sampler2D tex;
uniform float time;
uniform vec2 center;

in vec2 pos;

out vec4 fColor;


void main() {
    // init
    time; center;
    vec4 cur = texture(tex, pos);
    vec3 color = vec3(pos.y, pos.x, 1);
    fColor = vec4(cur.r, cur.g, cur.b, 1.0);
}