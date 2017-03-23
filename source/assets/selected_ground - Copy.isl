surface {
    blend: alpha,
  double-sided: true
}
in {
	vec3 pos_touched = vec3(0.0, 0.0, 0.0);
}

variant {
	vertex {
		out {
			vec3 p;
			vec3 n;
		}

		source %{
			%out.position% = _mtx_mul(vModelViewProjectionMatrix, vec4(vPosition, 1.0));

            p = (vModelMatrix * vec4(vPosition, 1.0)).xyz;
            n = normalize(vNormalMatrix * vNormal);
		%}
	}

	pixel {
		global %{
           #define time vClock*0.05
            #define tau 6.2831853

                //
                // Description : Array and textureless GLSL 2D simplex noise function.
                //      Author : Ian McEwan, Ashima Arts.
                //  Maintainer : stegu
                //     Lastmod : 20110822 (ijm)
                //     License : Copyright (C) 2011 Ashima Arts. All rights reserved.
                //               Distributed under the MIT License. See LICENSE file.
                //               https://github.com/ashima/webgl-noise
                //               https://github.com/stegu/webgl-noise
                //

                vec3 mod289(vec3 x) {
                  return x - floor(x * (1.0 / 289.0)) * 289.0;
                }

                vec2 mod289(vec2 x) {
                  return x - floor(x * (1.0 / 289.0)) * 289.0;
                }

                vec3 permute(vec3 x) {
                  return mod289(((x*34.0)+1.0)*x);
                }

                float snoise(vec2 v)
                  {
                  const vec4 C = vec4(0.211324865405187,  // (3.0-sqrt(3.0))/6.0
                                      0.366025403784439,  // 0.5*(sqrt(3.0)-1.0)
                                     -0.577350269189626,  // -1.0 + 2.0 * C.x
                                      0.024390243902439); // 1.0 / 41.0
                // First corner
                  vec2 i  = floor(v + dot(v, C.yy) );
                  vec2 x0 = v -   i + dot(i, C.xx);

                // Other corners
                  vec2 i1;
                  //i1.x = step( x0.y, x0.x ); // x0.x > x0.y ? 1.0 : 0.0
                  //i1.y = 1.0 - i1.x;
                  i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
                  // x0 = x0 - 0.0 + 0.0 * C.xx ;
                  // x1 = x0 - i1 + 1.0 * C.xx ;
                  // x2 = x0 - 1.0 + 2.0 * C.xx ;
                  vec4 x12 = x0.xyxy + C.xxzz;
                  x12.xy -= i1;

                // Permutations
                  i = mod289(i); // Avoid truncation effects in permutation
                  vec3 p = permute( permute( i.y + vec3(0.0, i1.y, 1.0 ))
                        + i.x + vec3(0.0, i1.x, 1.0 ));

                  vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy), dot(x12.zw,x12.zw)), 0.0);
                  m = m*m ;
                  m = m*m ;

                // Gradients: 41 points uniformly over a line, mapped onto a diamond.
                // The ring size 17*17 = 289 is close to a multiple of 41 (41*7 = 287)

                  vec3 x = 2.0 * fract(p * C.www) - 1.0;
                  vec3 h = abs(x) - 0.5;
                  vec3 ox = floor(x + 0.5);
                  vec3 a0 = x - ox;

                // Normalise gradients implicitly by scaling m
                // Approximation of: m *= inversesqrt( a0*a0 + h*h );
                  m *= 1.79284291400159 - 0.85373472095314 * ( a0*a0 + h*h );

                // Compute final noise value at P
                  vec3 g;
                  g.x  = a0.x  * x0.x  + h.x  * x0.y;
                  g.yz = a0.yz * x12.xz + h.yz * x12.yw;
                  return 130.0 * dot(m, g);
                }


            mat2 makem2(in float theta){float c = cos(theta);float s = sin(theta);return mat2(c,-s,s,c);}

            float fbm(in vec2 p)
            {
                float z=2.;
                float rz = 0.;
                vec2 bp = p;
                for (float i= 1.;i < 6.;i++)
                {
                    rz+= abs((snoise(p)-0.5)*2.)/z;
                    z = z*2.;
                    p = p*2.;
                }
                return rz;
            }

            float dualfbm(in vec2 p)
            {
                //get two rotated fbm calls and displace the domain
                vec2 p2 = p*.7;
                vec2 basis = vec2(fbm(p2-time*1.6),fbm(p2+time*1.7));
                basis = (basis-.5)*.2;
                p += basis;

                //coloring
                return fbm(p*makem2(time*0.2));
            }

            float circ(vec2 p)
            {
                float r = length(p);
                r = log(sqrt(r));
                return abs(mod(r*4.,tau)-3.14)*3.+.2;
            }

        %}

		source %{
		    vec3 v = pos_touched - p;
		    float dist = sqrt(dot(v, v));
		    float max_dist = 1.0;

		    if(dist > 50.)
		        discard;

            v = v / max_dist;
            vec2 p2 = vec2(v.x, v.z);
            p2 *= 4.;

		    if(dist > max_dist)
		    {
                if(max(abs(cos(p.x*20.)), abs(cos(p.z*20.))) <= 0.999)
                    discard;

                float dist_fall_off = 1.6;
                float fall_off = clamp((dist - max_dist) / (dist_fall_off - max_dist), 0, 1);
               %diffuse% = vec3(0, 1, 1);
                p2 /= exp(mod(time*10.,3.14159));
               %opacity% = 0.5 * fall_off * (1.0 - clamp(pow(abs((0.1-circ(p2))),.9), 0, 1));
		    }
            else
            {
                float dist_fall_off = 0.6;
                float fall_off = 1.0 - (dist - dist_fall_off) / (max_dist - dist_fall_off);

                float rz = dualfbm(p2);

                //rings
                p2 /= exp(mod(time*10.,3.14159));
                rz *= pow(abs((0.1-circ(p2))),.9);

                //final color
             //   vec3 col = vec3(.2,0.1,0.4)/rz;
               vec3 col = vec3(1.,0.33,0.)/rz;
               col = pow(abs(col),vec3(.99));
               %diffuse% = col;
               %opacity% = col.x * fall_off;
            }
		%}
	}
}
