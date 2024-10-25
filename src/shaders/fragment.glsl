#version 330 core

uniform sampler2D tex;
uniform sampler2D paletteTex;

uniform float time;
uniform vec2 center;
uniform vec2 res;
uniform vec2 rOffset;
uniform vec2 gOffset;
uniform vec2 bOffset;
uniform vec4 deadZone;

in vec2 pos;

out vec4 fColor;


float colorDiff(vec4 c1, vec4 c2) {
    return sqrt(pow(c2.r - c1.r, 2) + pow(c2.g - c1.g, 2) + pow(c2.b - c1.b, 2));
}


bool aabb(vec2 point, vec4 area) {
    return (point.x >= area.x && point.x <= area.x + area.z && point.y >= area.y && point.y <= area.y + area.w);
}

vec3 convertColorToPalette(vec4 cur) {
    vec2 paletteSize = vec2(textureSize(paletteTex, 0));
    float closestDistance = 2;
    vec3 closestColor = vec3(-1, -1, -1);
    for (int i = 0; i < paletteSize.x; i++) {
        vec4 paletteColor = texture(paletteTex, vec2(i / paletteSize.x, 0));
        float dist = colorDiff(paletteColor, cur);
        if (dist < closestDistance) {
            closestDistance = dist;
            closestColor = paletteColor.rgb;
        }
    }
    // IMPORTANT BECAUSE OF BRGRA OPENGL MADNESS!!
    return closestColor.bgr;
}


void main() {
    // init
    vec3 color;

    time; center; paletteTex; rOffset; gOffset; bOffset;
    vec4 cur = texture(tex, pos);
    
    if (aabb(pos * res, deadZone)) {
        color = cur.rgb;
    }
    else {
        color = convertColorToPalette(cur);
    }

    fColor = vec4(color, 1);
}