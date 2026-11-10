/* Board compositor. Sprites stay in GPU textures. Canvas 2D rasterizes the
   existing vector artwork, gradients and text into transparent passes. */
window.createFlowerBoardRenderer = function (canvas) {
  const paint = canvas.getContext("2d");
  const fallback = { ctx: paint, begin() {}, end() {}, clip(path) { paint.clip(path); } };
  if (new URLSearchParams(location.search).get("boardRenderer") === "2d") return fallback;
  const surface = document.createElement("canvas");
  let gl;
  try {
    gl = surface.getContext("webgl", { alpha: true, premultipliedAlpha: true, antialias: false });
  } catch (_) { return fallback; }
  if (!gl) return fallback;

  function shader(type, source) {
    const compiled = gl.createShader(type);
    gl.shaderSource(compiled, source);
    gl.compileShader(compiled);
    if (!gl.getShaderParameter(compiled, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(compiled));
    return compiled;
  }

  const program = gl.createProgram();
  try {
    gl.attachShader(program, shader(gl.VERTEX_SHADER, `
      precision mediump float;
      attribute vec2 corner;
      uniform vec2 origin, axisX, axisY, size;
      varying vec2 uv;
      void main() {
        uv = corner;
        vec2 p = (origin + axisX * uv.x + axisY * uv.y) / size;
        gl_Position = vec4(2.0 * p.x - 1.0, 1.0 - 2.0 * p.y, 0.0, 1.0);
      }`));
    gl.attachShader(program, shader(gl.FRAGMENT_SHADER, `
      precision mediump float;
      uniform sampler2D picture, boardMask;
      uniform vec2 size, maskSpan;
      uniform float opacity, clipped;
      varying vec2 uv;
      void main() {
        vec2 p = vec2(gl_FragCoord.x, size.y - gl_FragCoord.y);
        float mask = clipped > 0.5 ? texture2D(boardMask, p / maskSpan).r : 1.0;
        gl_FragColor = texture2D(picture, uv) * (opacity * mask);
      }`));
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program));
  } catch (err) {
    console.warn("Flower Fever board WebGL unavailable", err);
    return fallback;
  }

  const buffer = gl.createBuffer();
  gl.useProgram(program);
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([0, 0, 1, 0, 0, 1, 1, 1]), gl.STATIC_DRAW);
  const corner = gl.getAttribLocation(program, "corner");
  gl.enableVertexAttribArray(corner);
  gl.vertexAttribPointer(corner, 2, gl.FLOAT, false, 0, 0);
  const uniform = Object.fromEntries(
    ["origin", "axisX", "axisY", "size", "picture", "boardMask", "maskSpan", "opacity", "clipped"]
      .map(name => [name, gl.getUniformLocation(program, name)])
  );
  gl.uniform1i(uniform.picture, 0);
  gl.uniform1i(uniform.boardMask, 1);
  gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, true);
  gl.enable(gl.BLEND);
  gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);

  function texture(filter) {
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, filter);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, filter);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    return tex;
  }
  const vectorTexture = texture(gl.LINEAR);
  gl.activeTexture(gl.TEXTURE1);
  const maskTexture = texture(gl.NEAREST);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE,
    new Uint8Array([255, 255, 255, 255]));
  gl.activeTexture(gl.TEXTURE0);
  const textures = new Map();
  const cacheLimit = 96;
  let enabled = true, dirty = false, boardClip = false, localClips = 0, lastMask = null;
  const clips = [];

  surface.setAttribute("aria-hidden", "true");
  surface.dataset.boardRenderer = "webgl";
  Object.assign(surface.style, { position: "absolute", pointerEvents: "none" });
  canvas.after(surface);
  canvas.style.opacity = "0";
  surface.addEventListener("webglcontextlost", event => {
    event.preventDefault();
    enabled = false;
    surface.remove();
    canvas.style.opacity = "";
  });

  function quad(tex, x, y, ax, ay, bx, by, opacity, clipped) {
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.uniform2f(uniform.origin, x, y);
    gl.uniform2f(uniform.axisX, ax, ay);
    gl.uniform2f(uniform.axisY, bx, by);
    gl.uniform1f(uniform.opacity, opacity);
    gl.uniform1f(uniform.clipped, clipped ? 1 : 0);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  }

  function flushVectors() {
    if (!enabled || !dirty) return;
    gl.bindTexture(gl.TEXTURE_2D, vectorTexture);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, canvas);
    quad(vectorTexture, 0, 0, canvas.width, 0, 0, canvas.height, 1, false);
    paint.save();
    paint.setTransform(1, 0, 0, 1, 0, 0);
    paint.clearRect(0, 0, canvas.width, canvas.height);
    paint.restore();
    dirty = false;
  }

  function drawImage(image, ...rect) {
    if (!enabled || localClips || rect.length !== 4) {
      if (enabled) dirty = true;
      paint.drawImage(image, ...rect);
      return;
    }
    if (!image.width || !image.height) return;
    flushVectors();
    let tex = textures.get(image);
    if (tex) {
      textures.delete(image);
    } else {
      if (textures.size >= cacheLimit) {
        const oldest = textures.keys().next().value;
        gl.deleteTexture(textures.get(oldest));
        textures.delete(oldest);
      }
      tex = texture(gl.LINEAR);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, image);
    }
    textures.set(image, tex);
    const [x, y, width, height] = rect;
    const m = paint.getTransform();
    quad(tex, m.a * x + m.c * y + m.e, m.b * x + m.d * y + m.f,
      m.a * width, m.b * width, m.c * height, m.d * height, paint.globalAlpha, boardClip);
  }

  const rasterOps = new Set(["fill", "stroke", "fillRect", "strokeRect", "fillText", "strokeText"]);
  const methods = {
    drawImage,
    save() {
      clips.push([boardClip, localClips]);
      paint.save();
    },
    restore() {
      const clip = clips.pop();
      if (clip && (clip[0] !== boardClip || clip[1] !== localClips)) flushVectors();
      if (clip) [boardClip, localClips] = clip;
      paint.restore();
    },
    clip(...args) {
      flushVectors();
      paint.clip(...args);
      localClips++;
    }
  };
  const ctx = new Proxy(paint, {
    get(target, key) {
      if (Object.hasOwn(methods, key)) return methods[key];
      const value = target[key];
      if (typeof value !== "function") return value;
      const method = rasterOps.has(key) ? (...args) => {
        dirty = true;
        return value.apply(target, args);
      } : value.bind(target);
      methods[key] = method;
      return method;
    },
    set(target, key, value) {
      target[key] = value;
      return true;
    }
  });

  let layoutKey;
  return {
    ctx,
    begin() {
      if (!enabled) return;
      const key = [canvas.width, canvas.height, canvas.style.cssText].join(":");
      if (layoutKey !== key) {
        layoutKey = key;
        surface.width = canvas.width;
        surface.height = canvas.height;
        surface.style.left = canvas.offsetLeft + "px";
        surface.style.top = canvas.offsetTop + "px";
        surface.style.width = canvas.style.width;
        surface.style.height = canvas.style.height;
        surface.style.transform = canvas.style.transform;
        gl.viewport(0, 0, surface.width, surface.height);
        gl.uniform2f(uniform.size, surface.width, surface.height);
      }
      gl.clear(gl.COLOR_BUFFER_BIT);
    },
    clip(path, mask, cellSize) {
      flushVectors();
      paint.clip(path);
      if (!enabled) return;
      boardClip = true;
      const rows = mask.length, cols = mask[0].length;
      if (mask !== lastMask) {
        lastMask = mask;
        const pixels = new Uint8Array(rows * cols * 4);
        for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
          pixels[4 * (r * cols + c)] = mask[r][c] === 1 ? 255 : 0;
          pixels[4 * (r * cols + c) + 3] = 255;
        }
        gl.activeTexture(gl.TEXTURE1);
        gl.bindTexture(gl.TEXTURE_2D, maskTexture);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, cols, rows, 0, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
        gl.activeTexture(gl.TEXTURE0);
      }
      gl.uniform2f(uniform.maskSpan, cols * cellSize, rows * cellSize);
    },
    end: flushVectors
  };
};
