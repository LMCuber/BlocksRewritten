#version 330 core

uniform sampler2D tex;
uniform sampler2D paletteTex;

uniform float time;
uniform vec3 pink;
uniform vec2 res;
uniform vec2 rOffset;
uniform vec2 gOffset;
uniform vec2 bOffset;
uniform vec4 deadZone;
uniform bool grayscale;
uniform float blurSigma;
uniform bool palettize;

uniform float pi = 3.14159;

in vec2 pos;

out vec4 fColor;

// global variables
vec2 pix = vec2(1.0, 1.0) / res;

// F U N C T I O N S
vec3 rgb_to_gray(vec3 c) {
    return c == pink ? pink : vec3(0.2989 * c.r + 0.5870 * c.g + 0.1140 * c.b);
}

float colorDiff(vec4 c1, vec4 c2) {
    return sqrt(pow(c2.r - c1.r, 2) + pow(c2.g - c1.g, 2) + pow(c2.b - c1.b, 2));
}

bool aabb(vec2 point, vec4 area) {
    return (point.x >= area.x && point.x <= area.x + area.z && point.y >= area.y && point.y <= area.y + area.w);
}

vec4 palettizeColor(vec4 cur) {
    vec2 paletteSize = vec2(textureSize(paletteTex, 0));
    float closestDistance = 2;
    vec4 closestColor = vec4(-1, -1, -1, 0);
    for (int i = 0; i < paletteSize.x; i++) {
        vec4 paletteColor = texture(paletteTex, vec2(i / paletteSize.x, 0));
        float dist = colorDiff(paletteColor, cur);
        if (dist < closestDistance) {
            closestDistance = dist;
            closestColor = paletteColor;
        }
    }
    return closestColor;
}

vec3 chromab(vec2 pos) {
    float r = palettizeColor(texture(tex, pos + vec2(rOffset.x / res.x, rOffset.y / res.y))).r;
    float g = palettizeColor(texture(tex, pos + vec2(gOffset.x / res.x, gOffset.y / res.y))).g;
    float b = palettizeColor(texture(tex, pos + vec2(bOffset.x / res.x, bOffset.y / res.y))).b;
    return vec3(r, g, b);
}

float gauss(float d, float s) {
    return 1 / sqrt(2 * pi * pow(s, 2)) * exp(-(pow(d, 2)) / (2 * pow(s, 2)));
}

vec3 gaussianBlur(vec2 pos, float sigma) {
    vec4 avg = vec4(0.0, 0.0, 0.0, 0.0);
    int blurRadius = min(int(sigma * 3.0), 10);
    float d, weight, totalWeight;

    for (int yo = -blurRadius; yo < blurRadius + 1; yo ++) {
        for (int xo = -blurRadius; xo < blurRadius + 1; xo ++) {
            if (xo != 0 || yo != 0) {
                d = length(vec2(xo, yo));
                weight = gauss(d, sigma);
                avg += weight * texture(tex, pos - pix * vec2(xo, yo));
                totalWeight += weight;
            }
        }
    }
    avg /= totalWeight;
    return avg.rgb;
}

void main() {
    // safe
    time; paletteTex; rOffset; gOffset; bOffset; pink;

    // initializen variabeln
    vec4 color;
    vec4 cur = texture(tex, pos);

    // check dead areas
    if (aabb(pos * res, deadZone)) {
        fColor = cur;
        return;
    }

    // gaussian blur
    if (blurSigma > 0.3) {
        color = vec4(gaussianBlur(pos, blurSigma).rgb, texture(tex, pos).a);
    } else {
        color = vec4(texture(tex, pos));
    }

    // palettize after blur
    if (palettize) {
        color = palettizeColor(color);
    }

    // when grayscale, then just make it grayscale
    if (grayscale) {
        // color = vec4(rgb_to_gray(color.rgb), cur.a);
        color = vec4(color.rgb, cur.a);
    }

    // S E T  F I N A L  C O L O R
    fColor = color;
}