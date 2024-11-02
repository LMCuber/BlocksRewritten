#version 330 core

uniform sampler2D tex;
uniform sampler2D paletteTex;

uniform float time;
uniform vec2 centerWin;
uniform vec2 res;
uniform vec2 rOffset;
uniform vec2 gOffset;
uniform vec2 bOffset;
uniform vec4 deadZone;

uniform float shockForce;
uniform float shockSize;
uniform float shockThickness;
uniform vec2 shockPos;
uniform bool shockActive;
uniform vec2 lightPosWin;
uniform float lightPowerWin;

uniform float pi = 3.14159;
uniform float maxDistToCenter = 0.5 * sqrt(2.0);

in vec2 pos;

out vec4 fColor;


float colorDiff(vec4 c1, vec4 c2) {
    return sqrt(pow(c2.r - c1.r, 2) + pow(c2.g - c1.g, 2) + pow(c2.b - c1.b, 2));
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

vec3 chromab(vec4 color, vec2 pos, bool pallet, bool dropoff) {
    float r = palettize(texture(tex, pos + vec2(rOffset.x / res.x, rOffset.y / res.y))).r;
    float g = palettize(texture(tex, pos + vec2(gOffset.x / res.x, gOffset.y / res.y))).g;
    float b = palettize(texture(tex, pos + vec2(bOffset.x / res.x, bOffset.y / res.y))).b;
    return vec3(r, g, b);
}

void main() {
    // initializen variabeln
    float r, g, b, a;
    vec3 color;
    float dyDx = res.y / res.x;
    time; paletteTex; rOffset; gOffset; bOffset;
    vec2 center = centerWin / res;
    vec4 cur = texture(tex, pos);
    vec2 scaledPos = vec2((pos.x - 0.5) / dyDx + 0.5, pos.y);

    // cheeck foor deaad aareas
    if (aabb(pos * res, deadZone)) {
        fColor = cur;
        return;
    }

    // color palette
    // color = palettize(cur);

    // chromatic aberration
    color = chromab(cur, pos, true, true);

    // color = texture(tex, pos).rgb;

    if (shockActive) {
        vec2 scaledPos = (pos - vec2(0.5, 0.0)) / vec2(dyDx, 1.0) + vec2(0.5, 0.0);
        scaledPos = pos;
        float mask = (1 - smoothstep(shockSize - 0.1, shockSize, length(scaledPos - shockPos)))
                    * smoothstep(shockSize - shockThickness - 0.1, shockSize - shockThickness, length(scaledPos - shockPos));
        vec2 disp = normalize(scaledPos - shockPos) * shockForce * mask;
        color = texture(tex, pos - disp).rgb;
    }

    lightPosWin; lightPowerWin;

    // set final color
    fColor = vec4(color, texture(tex, pos).a);
}