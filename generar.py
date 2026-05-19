#!/usr/bin/env python3
"""
Meta Ads Creative Generator
Genera 100 creativos estáticos para Meta Ads usando Gemini AI y Pillow
"""

import os
import sys
import json
import re
import time
import subprocess
from pathlib import Path
from datetime import datetime

# ── Auto-install ──────────────────────────────────────────────────────────────
_PACKAGES = [
    ("google-generativeai", "google"),
    ("Pillow", "PIL"),
    ("python-dotenv", "dotenv"),
]

def _ensure_packages():
    missing = []
    for pkg, mod in _PACKAGES:
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"\n📦 Instalando dependencias: {', '.join(missing)} ...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install"] + missing + ["-q"],
        )
        print("   ✓ Dependencias instaladas\n")

_ensure_packages()

from dotenv import load_dotenv, set_key
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai

# ── Constantes ────────────────────────────────────────────────────────────────

FORMATS = [
    ("cuadrado", 1080, 1080),
    ("portrait", 1080, 1350),
]

ANGLES = {
    "dolor":        20,
    "deseo":        20,
    "objecion":     15,
    "transformacion": 15,
    "urgencia":     15,
    "prueba_social": 15,
}

ANGLE_BATCHES = [
    {"dolor": 20, "deseo": 20},
    {"objecion": 15, "transformacion": 15, "urgencia": 15, "prueba_social": 15},
]

ANGLE_DESC = {
    "dolor":         "toca el dolor más profundo, el problema que los desvela a las 3am",
    "deseo":         "activa la aspiración y el sueño que quieren lograr",
    "objecion":      "derriba objeciones directamente antes de que las piensen",
    "transformacion": "muestra la transformación antes/después, el cambio de vida concreto",
    "urgencia":      "crea urgencia real: por qué actuar AHORA y no mañana",
    "prueba_social": "usa prueba social implícita, resultados reales, testimonios sugeridos",
}

GRADIENTS = [
    ((15, 15, 35), (60, 15, 80)),    # morado profundo
    ((8,  18, 45), (18, 55, 95)),    # azul oscuro
    ((35,  8,  8), (90, 25, 15)),    # rojo/carmesí
    ((8,  35, 18), (15, 75, 35)),    # verde oscuro
    ((35, 28,  8), (90, 65, 15)),    # dorado oscuro
    ((18, 28, 38), (35, 58, 75)),    # verde azulado
    ((25,  8, 35), (65, 18, 85)),    # violeta
    ((38, 15,  8), (85, 45, 15)),    # naranja quemado
]

# ── Setup / API Key ───────────────────────────────────────────────────────────

def setup_api_key() -> str:
    env_path = Path(".env")
    if not env_path.exists():
        env_path.write_text("", encoding="utf-8")

    load_dotenv(env_path, override=True)
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        print("\n" + "═" * 60)
        print("  🔑  CONFIGURAR GEMINI API KEY")
        print("═" * 60)
        print()
        print("  La API de Gemini es completamente GRATUITA.")
        print("  Seguí estos pasos para obtener tu key:")
        print()
        print("  1.  Abrí este link en tu navegador:")
        print("      → https://aistudio.google.com/apikey")
        print()
        print("  2.  Iniciá sesión con tu cuenta de Google")
        print()
        print("  3.  Hacé clic en el botón 'Create API Key'")
        print()
        print("  4.  Copiá la key generada (empieza con 'AIza...')")
        print()
        print("─" * 60)

        while True:
            key = input("  Pegá tu API key aquí: ").strip()
            if key:
                break
            print("  ⚠️  No puede estar vacía")

        set_key(str(env_path), "GEMINI_API_KEY", key)
        print("  ✅  Key guardada en .env\n")
        api_key = key

    return api_key


# ── Recolección de datos ──────────────────────────────────────────────────────

def ask(prompt: str) -> str:
    while True:
        val = input(f"  {prompt}: ").strip()
        if val:
            return val
        print("    ⚠️  Este campo es requerido")


def get_product_info() -> dict:
    print("\n" + "═" * 60)
    print("  📝  INFORMACIÓN DEL PRODUCTO")
    print("═" * 60 + "\n")

    nombre    = ask("🏷️   Nombre del producto o servicio")
    precio    = ask("💰  Precio (ej: $97, $197/mes, Gratis)")
    promesa   = ask("✨  Promesa principal (qué resultado logra el cliente)")
    audiencia = ask("👥  Audiencia objetivo")

    print("\n  💬  Ingresá 3 objeciones comunes de tu cliente ideal:")
    objeciones = [ask(f"     Objeción {i}") for i in range(1, 4)]

    return {
        "nombre":     nombre,
        "precio":     precio,
        "promesa":    promesa,
        "audiencia":  audiencia,
        "objeciones": objeciones,
    }


def get_backgrounds() -> list:
    print("\n" + "═" * 60)
    print("  🖼️   IMÁGENES DE FONDO")
    print("═" * 60)
    print()
    print("  ¿Qué fondos querés usar para los creativos?")
    print()
    print("  A → Mis propias imágenes  (ponelas en la carpeta /fondos/)")
    print("  B → Fondos automáticos   (gradientes de colores generados)")
    print()

    while True:
        choice = input("  Elegí A o B: ").strip().upper()
        if choice in ("A", "B"):
            break
        print("  ⚠️  Ingresá A o B")

    if choice == "B":
        print("\n  ✅  Se usarán gradientes automáticos")
        return []

    fondos_dir = Path("fondos")
    fondos_dir.mkdir(exist_ok=True)

    exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    images = [str(f) for f in fondos_dir.iterdir() if f.suffix.lower() in exts]

    if not images:
        print(f"\n  ⚠️  No encontré imágenes en /fondos/")
        print("     Copiá tus fotos ahí y volvé a correr el script.")
        print("\n  ¿Usar gradientes automáticos en su lugar? (s/n): ", end="")
        if input().strip().lower() == "s":
            return []
        sys.exit(0)

    print(f"\n  ✅  {len(images)} imagen(es) encontrada(s) en /fondos/")
    return images


# ── Generación de copies con Gemini ──────────────────────────────────────────

def _extract_json(text: str) -> dict:
    """Extrae JSON del texto, incluso si viene envuelto en markdown."""
    text = text.strip()
    # Remover bloques markdown ```json ... ```
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.strip().lstrip("json").strip()
            if part.startswith("{"):
                text = part
                break
    # Buscar el bloque JSON más externo
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return json.loads(match.group())
    raise ValueError("No se encontró JSON válido en la respuesta")


def generate_copies(product: dict, api_key: str) -> tuple:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    all_copies = []
    total_in   = 0
    total_out  = 0

    for batch_idx, batch in enumerate(ANGLE_BATCHES):
        angles_list = "\n".join(f"  - {a}: {n} variaciones" for a, n in batch.items())
        descs_list  = "\n".join(f"  - {a}: {ANGLE_DESC[a]}" for a in batch)

        # Para el ángulo de objeciones, inyectar las objeciones reales
        obj_note = ""
        if "objecion" in batch:
            obj_note = f"\nObjeciones reales del cliente: {', '.join(product['objeciones'])}"

        prompt = f"""Sos un experto copywriter de Meta Ads en español latinoamericano.

PRODUCTO: {product['nombre']}
PRECIO: {product['precio']}
PROMESA: {product['promesa']}
AUDIENCIA: {product['audiencia']}{obj_note}

Generá copies para estos ángulos:
{angles_list}

Descripción de cada ángulo:
{descs_list}

REGLAS ESTRICTAS:
- headline: máximo 8 palabras, impactante, directo, sin signos de exclamación al inicio
- subtitulo: máximo 15 palabras, que complemente y profundice el headline
- cta: 2 a 5 palabras, acción clara (ej: "Quiero empezar ya", "Accedé ahora", "Lo quiero hoy")
- Español latinoamericano natural, cero tecnicismos
- Sin emojis dentro del texto
- Cada copy debe sonar diferente al anterior. No repetir estructuras ni frases
- Que suenen escritos por una persona real, no un robot

Respondé ÚNICAMENTE con JSON válido, sin texto adicional, sin bloques markdown:
{{
  "copies": [
    {{"angulo": "nombre_angulo", "headline": "...", "subtitulo": "...", "cta": "..."}}
  ]
}}"""

        for attempt in range(3):
            try:
                resp = model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        temperature=0.88,
                        max_output_tokens=4096,
                    ),
                )

                if hasattr(resp, "usage_metadata") and resp.usage_metadata:
                    total_in  += resp.usage_metadata.prompt_token_count or 0
                    total_out += resp.usage_metadata.candidates_token_count or 0

                data   = _extract_json(resp.text)
                copies = data.get("copies", [])
                all_copies.extend(copies)

                expected = sum(batch.values())
                print(f"  ✓ Lote {batch_idx + 1}: {len(copies)}/{expected} copies  ({', '.join(batch)})")
                break

            except json.JSONDecodeError as e:
                if attempt == 2:
                    print(f"  ❌ No se pudo parsear el JSON del lote {batch_idx + 1}: {e}")
                    raise
                time.sleep(2)

            except Exception as e:
                msg = str(e)
                if any(k in msg for k in ("API_KEY_INVALID", "API key not valid", "INVALID_ARGUMENT")):
                    print("\n  ❌ La API Key de Gemini es inválida o fue revocada.")
                    print("     Obtené una nueva en: https://aistudio.google.com/apikey")
                    print("     Luego borrá la línea GEMINI_API_KEY del archivo .env")
                    print("     y volvé a correr el script.")
                    sys.exit(1)
                if attempt == 2:
                    raise
                print(f"  ⚠️  Intento {attempt + 1} fallido ({e}), reintentando...")
                time.sleep(3)

    return all_copies, total_in, total_out


# ── Renderizado ───────────────────────────────────────────────────────────────

def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = []
    if sys.platform == "win32":
        candidates = [
            f"C:/Windows/Fonts/{'arialbd' if bold else 'arial'}.ttf",
            f"C:/Windows/Fonts/{'calibrib' if bold else 'calibri'}.ttf",
            f"C:/Windows/Fonts/{'segoeuib' if bold else 'segoeui'}.ttf",
            "C:/Windows/Fonts/tahoma.ttf",
        ]
    elif sys.platform == "darwin":
        candidates = [
            f"/System/Library/Fonts/Supplemental/Arial{'%20Bold' if bold else ''}.ttf",
            "/Library/Fonts/Arial.ttf",
        ]
    else:
        candidates = [
            f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
            f"/usr/share/fonts/truetype/liberation/LiberationSans-{'Bold' if bold else 'Regular'}.ttf",
        ]

    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue

    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _text_width(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    try:
        return int(draw.textlength(text, font=font))
    except Exception:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]


def _wrap(text: str, font, max_w: int, draw: ImageDraw.ImageDraw) -> list:
    words = text.split()
    lines, current = [], []
    for word in words:
        test = " ".join(current + [word])
        if _text_width(draw, test, font) <= max_w:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines or [text]


def _make_gradient(w: int, h: int, c1: tuple, c2: tuple) -> Image.Image:
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        color = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
        draw.line([(0, y), (w, y)], fill=color)
    return img


def render_creative(
    bg_source,       # str (path) or tuple ((r,g,b),(r,g,b))
    w: int, h: int,
    product_name: str,
    headline: str,
    subtitle: str,
    cta: str,
) -> Image.Image:

    # Fondo
    if isinstance(bg_source, str):
        bg = Image.open(bg_source).convert("RGB").resize((w, h), Image.LANCZOS)
    else:
        bg = _make_gradient(w, h, bg_source[0], bg_source[1])

    # Overlay semitransparente para legibilidad
    img = bg.convert("RGBA")
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 158))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    PAD  = 64
    TW   = w - PAD * 2
    WHT  = (255, 255, 255, 255)
    LIT  = (210, 210, 210, 255)
    SHD  = (0,   0,   0,   200)

    # ── Nombre del producto (arriba centrado) ──
    f_prod = _get_font(34)
    pw = _text_width(draw, product_name, f_prod)
    draw.text(((w - pw) // 2 + 2, 52), product_name, font=f_prod, fill=SHD)
    draw.text(((w - pw) // 2,     50), product_name, font=f_prod, fill=LIT)

    # ── Headline (grande, centro-alto) ──
    hl_size = 84
    f_hl, lines_hl = None, []
    while hl_size >= 40:
        f_hl    = _get_font(hl_size, bold=True)
        lines_hl = _wrap(headline, f_hl, TW, draw)
        if len(lines_hl) <= 3:
            break
        hl_size -= 6

    lh_hl    = hl_size + 16
    total_hl = len(lines_hl) * lh_hl
    hl_y     = int(h * 0.28)

    for line in lines_hl:
        lw = _text_width(draw, line, f_hl)
        x  = (w - lw) // 2
        draw.text((x + 2, hl_y + 2), line, font=f_hl, fill=SHD)
        draw.text((x,     hl_y    ), line, font=f_hl, fill=WHT)
        hl_y += lh_hl

    # ── Subtítulo ──
    sub_y  = hl_y + 24
    f_sub  = _get_font(40)
    lines_sub = _wrap(subtitle, f_sub, TW, draw)

    for line in lines_sub:
        lw = _text_width(draw, line, f_sub)
        x  = (w - lw) // 2
        draw.text((x + 1, sub_y + 1), line, font=f_sub, fill=SHD)
        draw.text((x,     sub_y    ), line, font=f_sub, fill=LIT)
        sub_y += 54

    # ── Botón CTA (abajo) ──
    f_cta  = _get_font(38, bold=True)
    cta_tw = _text_width(draw, cta, f_cta)

    btn_w = cta_tw + 80
    btn_h = 72
    btn_x = (w - btn_w) // 2
    btn_y = h - 148

    # Sombra del botón
    draw.rectangle([btn_x + 4, btn_y + 4, btn_x + btn_w + 4, btn_y + btn_h + 4],
                   fill=(0, 0, 0, 120))
    # Botón
    draw.rectangle([btn_x, btn_y, btn_x + btn_w, btn_y + btn_h],
                   fill=(255, 200, 0, 255))

    # Texto del CTA
    cta_x = btn_x + (btn_w - cta_tw) // 2
    cta_y = btn_y + (btn_h - 38) // 2
    draw.text((cta_x, cta_y), cta, font=f_cta, fill=(18, 18, 18, 255))

    return img.convert("RGB")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "═" * 60)
    print("  🎨  META ADS CREATIVE GENERATOR")
    print("  Genera 100 creativos estáticos para Facebook e Instagram")
    print("═" * 60)

    # 1. API Key
    api_key = setup_api_key()

    # 2. Validar key rápido
    try:
        genai.configure(api_key=api_key)
        genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        print(f"\n  ❌ Error con la API key: {e}")
        sys.exit(1)

    # 3. Info del producto
    product = get_product_info()

    # 4. Fondos
    bg_paths = get_backgrounds()
    use_gradients = (len(bg_paths) == 0)

    # 5. Generar copies
    print("\n" + "═" * 60)
    print("  🤖  GENERANDO COPIES CON GEMINI AI")
    print("═" * 60 + "\n")

    copies, tok_in, tok_out = generate_copies(product, api_key)

    if not copies:
        print("\n  ❌ No se generaron copies. Intentá de nuevo.")
        sys.exit(1)

    print(f"\n  ✅ Total de copies: {len(copies)}")

    # 6. Directorio de salida
    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path("creativos") / ts

    angle_set = {c.get("angulo", "general") for c in copies}
    for angle in angle_set:
        for fmt_name, _, _ in FORMATS:
            (out_dir / angle / fmt_name).mkdir(parents=True, exist_ok=True)

    # 7. Renderizar
    print("\n" + "═" * 60)
    print("  🎨  RENDERIZANDO CREATIVOS")
    print("═" * 60)
    n_imgs = len(copies) * len(FORMATS)
    print(f"\n  {len(copies)} copies × {len(FORMATS)} formatos = {n_imgs} imágenes\n")

    rendered = 0
    errors   = 0

    for i, copy_data in enumerate(copies):
        angle    = copy_data.get("angulo", "general")
        headline = copy_data.get("headline", "").strip()
        subtitle = (copy_data.get("subtitulo") or copy_data.get("subtitle") or "").strip()
        cta      = (copy_data.get("cta") or "Quiero saber más").strip()

        if not headline:
            continue

        # Fondo a usar (mismo para ambos formatos del mismo copy)
        if use_gradients:
            bg_src = GRADIENTS[i % len(GRADIENTS)]
        else:
            bg_src = bg_paths[i % len(bg_paths)]

        for fmt_name, w, h in FORMATS:
            try:
                img  = render_creative(bg_src, w, h, product["nombre"], headline, subtitle, cta)
                fname     = f"{angle}_{i + 1:03d}_{fmt_name}.jpg"
                save_path = out_dir / angle / fmt_name / fname
                img.save(str(save_path), "JPEG", quality=93, optimize=True)
                rendered += 1
            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"  ⚠️  Error copy {i + 1} [{fmt_name}]: {e}")

        # Barra de progreso
        pct = (i + 1) / len(copies)
        bar = "█" * int(pct * 32) + "░" * (32 - int(pct * 32))
        print(f"\r  [{bar}] {i + 1}/{len(copies)}  ({rendered} imgs)", end="", flush=True)

    print()  # newline

    # 8. Resumen
    print("\n" + "═" * 60)
    print("  ✅  GENERACIÓN COMPLETADA")
    print("═" * 60)

    print(f"\n  📊 Resultados:")
    print(f"     Imágenes generadas : {rendered}")
    if errors:
        print(f"     Errores            : {errors}")
    print(f"     Ubicación          : creativos/{ts}/")

    print(f"\n  📁 Distribución por ángulo:")
    counts = {}
    for c in copies:
        a = c.get("angulo", "general")
        counts[a] = counts.get(a, 0) + 1
    for angle, n in sorted(counts.items()):
        print(f"     {angle:<22}  {n} copies × {len(FORMATS)} formatos = {n * len(FORMATS)} imgs")

    print(f"\n  🤖 Tokens Gemini usados:")
    print(f"     Input  : {tok_in:>8,}")
    print(f"     Output : {tok_out:>8,}")
    print(f"     Total  : {tok_in + tok_out:>8,}")

    cost = (tok_in / 1_000_000 * 0.075) + (tok_out / 1_000_000 * 0.30)
    print(f"\n  💰 Costo estimado: ~${cost:.4f} USD  (Gemini 1.5 Flash)")
    print(f"     Verificá precios actuales en: https://ai.google.dev/pricing")

    print(f"\n  🚀 ¡Listo! Tus creativos están en:")
    print(f"     {out_dir.absolute()}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  ⚠️  Cancelado por el usuario\n")
        sys.exit(0)
