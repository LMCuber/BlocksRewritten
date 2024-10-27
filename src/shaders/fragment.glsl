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

uniform float pi = 3.14159;
uniform float maxDistToCenter = 0.5 * sqrt(2.0);

in vec2 pos;

out vec4 fColor;


float colorDiff(vec4 c1, vec4 c2) {
    return sqrt(pow(c2.r - c1.r, 2) + pow(c2.g - c1.g, 2) + pow(c2.b - c1.b, 2));
}

float getDistToCenter(vec2 pos) {
    return sqrt(pow(pos.x - center.x / res.x, 2) + pow(pos.y - center.y / res.y, 2));
}


bool aabb(vec2 point, vec4 area) {
    return (point.x >= area.x && point.x <= area.x + area.z && point.y >= area.y && point.y <= area.y + area.w);
}

vec3 palettize(vec4 cur) {
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

vec3 chromab(vec4 color, vec2 pos, bool dropoff) {
    float power = dropoff? getDistToCenter(pos) / (maxDistToCenter * 5) : 1;
    float r = palettize(texture(tex, pos + vec2(rOffset.x / res.x * power, rOffset.y / res.y * power))).r;
    float g = palettize(texture(tex, pos + vec2(gOffset.x / res.x * power, gOffset.y / res.y * power))).g;
    float b = palettize(texture(tex, pos + vec2(bOffset.x / res.x * power, bOffset.y / res.y * power))).b;
    return vec3(r, g, b);
}

void main() {
    // initializen variabeln
    float r, g, b, a;
    vec3 color;
    time; center; paletteTex; rOffset; gOffset; bOffset;
    vec4 cur = texture(tex, pos);

    // cheeck foor deaad aareas
    if (aabb(pos * res, deadZone)) {
        fColor = cur;
        return;
    }

    // color palette
    color = palettize(cur);

    // chromatic aberration
    color = chromab(cur, pos, true);

    // set final color
    fColor = vec4(color, 1);
}