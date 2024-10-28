#version 330 core

uniform sampler2D tex;
uniform sampler2D paletteTex;

uniform float time;
uniform vec2 center;
uniform vec2 size;
uniform vec2 rOffset;
uniform vec2 gOffset;
uniform vec2 bOffset;

in vec2 pos;

out vec4 fColor;


void main() {
    // init

    float w = 1 / size.x;
    float h = 1 / size.y;

    time; center; paletteTex; rOffset; gOffset; bOffset;
    vec4 cur = texture(tex, pos);

    // float r = texture(tex, pos + vec2(rOffset.x * w, rOffset.y * h)).r;
    // float g = texture(tex, pos + vec2(gOffset.x * w, gOffset.y * h)).g;
    // float b = texture(tex, pos + vec2(bOffset.x * w, bOffset.y * h)).b;

    ivec2 paletteSize = textureSize(paletteTex, 0);
    for (int i = 0; i < paletteSize.x; i++) {

    }
    float r = 0.3;
    float g = 0.3;
    float b = 0.3;

    fColor = vec4(r, g, b, 1.0);
}