"""Renderiza el portafolio HTML a partir de datos ya validados."""

import base64
import hashlib
import html
import re

from seguridad import cv_incrustable, validar_contacto

ESTILOS_CSS = """
:root {
  --fondo: #f5f6fa;
  --tarjeta: #ffffff;
  --texto: #14181f;
  --atenuado: #5a6575;
  --borde: #e2e5ec;
  --acento: #3b5bdb;
  --acento-2: #7048e8;
  --acento-suave: #edf0ff;
  --sombra: 0 1px 2px rgba(20, 24, 31, 0.06), 0 4px 14px rgba(20, 24, 31, 0.04);
  --sombra-alta: 0 10px 30px rgba(59, 91, 219, 0.16);
  --l0: #3b82f6; --l1: #10b981; --l2: #f59e0b; --l3: #ef4444;
  --l4: #8b5cf6; --l5: #ec4899; --l6: #14b8a6; --l7: #f97316;
}

@media (prefers-color-scheme: dark) {
  :root {
    --fondo: #0b0f16;
    --tarjeta: #141b26;
    --texto: #e8ebf1;
    --atenuado: #9aa6b6;
    --borde: #252e3c;
    --acento: #8ea6ff;
    --acento-2: #b197fc;
    --acento-suave: #1b2438;
    --sombra: 0 1px 2px rgba(0, 0, 0, 0.4);
    --sombra-alta: 0 10px 30px rgba(0, 0, 0, 0.45);
  }
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }

body {
  margin: 0;
  background: var(--fondo);
  color: var(--texto);
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  line-height: 1.65;
  -webkit-font-smoothing: antialiased;
}

a { color: var(--acento); text-decoration: none; transition: color 0.15s ease; }
a:hover { text-decoration: underline; }
:focus-visible { outline: 3px solid var(--acento); outline-offset: 2px; border-radius: 4px; }

.contenedor { max-width: 920px; margin: 0 auto; padding: 0 1.5rem; }

.saltar {
  position: fixed; top: 0.75rem; left: 0.75rem; z-index: 100;
  padding: 0.5rem 0.9rem; border-radius: 8px;
  background: var(--acento); color: #ffffff; font-weight: 600;
  transform: translateY(calc(-100% - 2rem)); transition: transform 0.15s ease;
}
.saltar:focus, .saltar:focus-visible { transform: translateY(0); }

.banda {
  background:
    radial-gradient(circle at 15% 0%, rgba(255, 255, 255, 0.22), transparent 45%),
    linear-gradient(135deg, var(--acento), var(--acento-2));
  color: #ffffff;
  padding: 3.5rem 0 5.5rem;
}

.hero { display: flex; align-items: center; gap: 1.75rem; }

.avatar {
  flex-shrink: 0; width: 96px; height: 96px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: rgba(255, 255, 255, 0.18);
  border: 3px solid rgba(255, 255, 255, 0.7);
  color: #ffffff; font-size: 2.1rem; font-weight: 700; letter-spacing: 0.04em;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
}

.hero-texto { min-width: 0; }
.hero h1 { margin: 0; font-size: 2.4rem; line-height: 1.15; letter-spacing: -0.02em; overflow-wrap: break-word; }
.titular { margin: 0.45rem 0 0; font-size: 1.15rem; opacity: 0.92; max-width: 52ch; }

.metricas {
  list-style: none; display: flex; gap: 1rem; flex-wrap: wrap;
  margin: -2.6rem 0 0; padding: 0; position: relative;
}
.metricas li {
  flex: 1 1 140px; background: var(--tarjeta); border: 1px solid var(--borde);
  border-radius: 14px; padding: 0.9rem 1.1rem; box-shadow: var(--sombra);
}
.metricas strong { display: block; font-size: 1.7rem; line-height: 1.1; color: var(--acento); }
.metricas span { font-size: 0.85rem; color: var(--atenuado); }

.menu {
  display: flex; gap: 0.4rem; flex-wrap: wrap; margin: 1.6rem 0 0; padding: 0;
  list-style: none;
}
.menu a {
  display: inline-block; padding: 0.3rem 0.85rem; border-radius: 999px;
  background: var(--acento-suave); color: var(--acento); font-size: 0.9rem; font-weight: 600;
}
.menu a:hover { text-decoration: none; filter: brightness(0.96); }

/* --- Mapa lateral: menú fijo a la izquierda que sigue el desplazamiento ---
   El resaltado de la sección visible lo pone el script del final (IntersectionObserver);
   :target lo respalda cuando el navegador no ejecuta scripts. */
.mapa {
  position: fixed; top: 14rem; left: 1rem; z-index: 50;
  width: 13.5rem; box-sizing: border-box;
  display: flex; flex-direction: column; gap: 0.15rem;
  padding: 0.9rem 0.7rem; border-radius: 16px;
  background: var(--tarjeta); border: 1px solid var(--borde); box-shadow: var(--sombra);
}
.mapa-titulo {
  margin: 0 0 0.5rem; padding: 0 0.6rem; font-size: 0.78rem; font-weight: 700;
  letter-spacing: 0.08em; text-transform: uppercase; color: var(--atenuado);
}
.mapa ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 0.15rem; }
.mapa a {
  position: relative; display: flex; align-items: center; gap: 0.6rem;
  padding: 0.5rem 0.7rem; border-radius: 10px; font-size: 1rem; font-weight: 600;
  color: var(--atenuado); white-space: nowrap;
  transition: color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
}
.mapa a::before {
  content: ""; width: 9px; height: 9px; border-radius: 50%; flex: none;
  background: var(--borde); transition: background 0.15s ease, transform 0.15s ease;
}
.mapa a:hover { color: var(--acento); background: var(--acento-suave); text-decoration: none; }
.mapa a:hover::before { background: var(--acento); }
/* Sección en la que estás: el texto queda subrayado con una línea gruesa del color del
   acento (crece desde la izquierda) y el punto se rellena. El hover solo cambia el fondo,
   así los dos estados no se confunden. */
.mapa a::after {
  content: ""; position: absolute; left: 0.7rem; right: 0.7rem; bottom: 0.28rem;
  height: 3px; border-radius: 3px; background: var(--acento);
  transform: scaleX(0); transform-origin: left;
  transition: transform 0.25s ease;
}
.mapa a.activo { color: var(--acento); font-weight: 700; }
.mapa a.activo::before { background: var(--acento); transform: scale(1.3); }
.mapa a.activo::after { transform: scaleX(1); }
.mapa a:target { color: var(--acento); }
.mapa a:target::after { transform: scaleX(1); }
.seccion:target > h2 { color: var(--acento); }

.seccion { padding: 2.4rem 0 0.4rem; scroll-margin-top: 1rem; }
.seccion h2 {
  display: flex; align-items: center; gap: 0.6rem;
  margin: 0 0 1.2rem; font-size: 1.4rem; letter-spacing: -0.01em;
}
.seccion h2::before {
  content: ""; width: 5px; height: 1.4rem; border-radius: 3px;
  background: linear-gradient(var(--acento), var(--acento-2));
}

.sobre-mi p {
  max-width: 66ch;
  margin: 0 0 1rem;
  font-size: 1.04rem;
  line-height: 1.75;

  text-align: justify;
  text-align-last: left;

  text-justify: inter-word;
  hyphens: auto;
  -webkit-hyphens: auto;
  hyphenate-limit-chars: 6 3 3;
  overflow-wrap: break-word;
}

.sobre-mi p:first-of-type {
  font-size: 1.15rem;
}
.sobre-mi p:last-child { margin-bottom: 0; }

.chips { list-style: none; display: flex; flex-wrap: wrap; gap: 0.55rem; margin: 0; padding: 0; }
.chips li {
  border: 1px solid var(--borde); background: var(--tarjeta);
  border-radius: 999px; padding: 0.4rem 1rem; font-size: 0.92rem; font-weight: 500;
  box-shadow: var(--sombra); transition: border-color 0.15s ease, transform 0.15s ease;
}
.chips li:hover { border-color: var(--acento); transform: translateY(-1px); }

.chips.contacto li { padding: 0; }
.boton-contacto { display: block; padding: 0.55rem 1.2rem; font-weight: 600; color: var(--acento); }
.boton-contacto:hover { text-decoration: none; background: var(--acento-suave); border-radius: 999px; }
.boton-contacto[download] { color: var(--acento-2); }
.contacto-dato { margin: 0.9rem 0 0; color: var(--atenuado); font-size: 0.95rem; overflow-wrap: anywhere; }

.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1.1rem; }

.tarjeta {
  position: relative; display: flex; flex-direction: column; gap: 0.55rem;
  background: var(--tarjeta); border: 1px solid var(--borde); border-radius: 16px;
  padding: 1.35rem 1.35rem 1.25rem; box-shadow: var(--sombra); overflow: hidden;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}
.tarjeta::before {
  content: ""; position: absolute; inset: 0 0 auto 0; height: 4px;
  background: linear-gradient(90deg, var(--acento), var(--acento-2), var(--acento));
}
.tarjeta:hover { transform: translateY(-3px); box-shadow: var(--sombra-alta); border-color: var(--acento); }

.titulo-proyecto { margin: 0.2rem 0 0; font-size: 1.1rem; line-height: 1.3; overflow-wrap: break-word; }
.titulo-proyecto a { color: var(--texto); }
.titulo-proyecto a:hover { color: var(--acento); text-decoration: none; }

.lenguaje { margin: 0; }
.chip-lenguaje {
  display: inline-flex; align-items: center; gap: 0.4rem;
  font-size: 0.82rem; color: var(--atenuado); font-weight: 500;
}
.chip-lenguaje::before {
  content: ""; width: 0.7rem; height: 0.7rem; border-radius: 50%; background: var(--l0);
}
.l1::before { background: var(--l1); } .l2::before { background: var(--l2); }
.l3::before { background: var(--l3); } .l4::before { background: var(--l4); }
.l5::before { background: var(--l5); } .l6::before { background: var(--l6); }
.l7::before { background: var(--l7); }

.descripcion { margin: 0; color: var(--atenuado); font-size: 0.95rem; overflow-wrap: break-word; }

.ver {
  margin: auto 0 0; padding-top: 0.4rem; font-size: 0.9rem; font-weight: 600;
}

footer {
  margin-top: 3rem; border-top: 1px solid var(--borde); color: var(--atenuado);
  font-size: 0.85rem; padding: 1.4rem 0 2.8rem;
}
footer p { margin: 0; }

@media (max-width: 1180px) {
  .mapa { display: none; }
}

@media (max-width: 600px) {
  .contenedor { padding-left: 1rem; padding-right: 1rem; }
  .banda { padding: 2.2rem 0 4.8rem; }
  .hero { flex-direction: column; align-items: flex-start; gap: 1rem; }
  .avatar { width: 76px; height: 76px; font-size: 1.7rem; }
  .hero h1 { font-size: 1.85rem; }
}

/* --- Animaciones (solo CSS, sin scripts) --- */
@keyframes gipp-aparecer {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: none; }
}
@keyframes gipp-flotar {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}
@keyframes gipp-brillo {
  from { background-position: 0% 50%; }
  to { background-position: 200% 50%; }
}
@keyframes gipp-latido {
  0%, 100% { box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18); }
  50% { box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3); }
}

.hero { animation: gipp-aparecer 0.6s ease-out both; }
.metricas li { animation: gipp-aparecer 0.5s ease-out both; }
.metricas li:nth-child(2) { animation-delay: 0.08s; }
.metricas li:nth-child(3) { animation-delay: 0.16s; }
.menu li { animation: gipp-aparecer 0.5s ease-out both; }
.menu li:nth-child(2) { animation-delay: 0.05s; }
.menu li:nth-child(3) { animation-delay: 0.1s; }
.menu li:nth-child(4) { animation-delay: 0.15s; }
.tarjeta { animation: gipp-aparecer 0.5s ease-out both; }
.tarjeta:nth-child(2) { animation-delay: 0.07s; }
.tarjeta:nth-child(3) { animation-delay: 0.14s; }
.tarjeta:nth-child(4) { animation-delay: 0.21s; }
.tarjeta:nth-child(5) { animation-delay: 0.28s; }
.tarjeta:nth-child(6) { animation-delay: 0.35s; }
.chips li { animation: gipp-aparecer 0.4s ease-out both; }
.chips li:nth-child(2n) { animation-delay: 0.04s; }
.chips li:nth-child(3n) { animation-delay: 0.08s; }
.tarjeta::before {
  background-size: 200% 100%;
  animation: gipp-brillo 6s linear infinite;
}
.boton-contacto { transition: background 0.15s ease, transform 0.15s ease; }
.boton-contacto:hover { transform: translateY(-2px); }
.seccion h2::before { transition: transform 0.2s ease; }
.seccion h2:hover::before { transform: scaleY(1.15); }

/* --- Animaciones al entrar en pantalla (solo CSS, sin scripts) ---
   animation-timeline: view() no está en el estándar estable: los navegadores que no la
   soportan ignoran la declaración y dejan la animación normal de arriba. */
@keyframes gipp-entrar {
  from { opacity: 0; transform: translateY(28px) scale(0.985); }
  to { opacity: 1; transform: none; }
}
@supports (animation-timeline: view()) {
  .seccion {
    animation: gipp-entrar linear both;
    animation-timeline: view();
    animation-range: entry 0% cover 32%;
  }
  .seccion .tarjeta, .seccion .chips li {
    animation: gipp-entrar linear both;
    animation-timeline: view();
    animation-range: entry 0% cover 45%;
  }
}

/* --- Subrayado que crece al pasar el ratón --- */
.titulo-proyecto a, .ver a, .menu a { position: relative; }
.titulo-proyecto a::after, .ver a::after {
  content: ""; position: absolute; left: 0; right: 0; bottom: -2px; height: 2px;
  background: currentColor; border-radius: 2px;
  transform: scaleX(0); transform-origin: left;
  transition: transform 0.25s ease;
}
.titulo-proyecto a:hover::after, .ver a:hover::after { transform: scaleX(1); }

/* --- Icono del avatar: flotación suave --- */
.avatar { animation: gipp-aparecer 0.6s ease-out both, gipp-latido 4s ease-in-out 1s infinite, gipp-flotar 5s ease-in-out 1.2s infinite; }

@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  .saltar, .tarjeta, .chips li, a, .boton-contacto, .seccion h2::before,
  .titulo-proyecto a::after, .ver a::after, .mapa a::after { transition: none; }
  .hero, .avatar, .metricas li, .menu li, .tarjeta, .chips li, .tarjeta::before, .seccion {
    animation: none !important;
  }
}

@media print {
  * { animation: none !important; transition: none !important; }
  .titulo-proyecto a::after, .ver a::after, .mapa a::after { display: none; }
  body { background: #ffffff; color: #000000; }
  .banda { background: #ffffff; color: #000000; padding: 0 0 1rem; border-bottom: 2px solid #333333; }
  .avatar { display: none; }
  .metricas, .menu, .mapa, .saltar { display: none; }
  .titular, .descripcion, .chip-lenguaje, footer { color: #333333; opacity: 1; }
  .tarjeta, .chips li { background: #ffffff; box-shadow: none; border-color: #c8ccd2; }
  .tarjeta { break-inside: avoid; }
  .tarjeta::before { display: none; }
  a { color: #1f409e; text-decoration: underline; }
}
"""

TEMAS = {
    "moderno": ("Moderno", ""),
    "dark-hack": ("Dark Hack (terminal oscuro)", """
:root {
  --fondo: #080b08; --tarjeta: #0e130e; --texto: #d6f5d6; --atenuado: #8aa88a;
  --borde: #1f2e1f; --acento: #39ff88; --acento-2: #00c2a8; --acento-suave: #12201a;
  --sombra: none; --sombra-alta: 0 0 22px rgba(57, 255, 136, 0.22);
}
body { font-family: ui-monospace, "Cascadia Code", "SF Mono", Consolas, "Courier New", monospace; }
.banda { background: #0b100b; border-bottom: 1px solid var(--borde); color: var(--texto); padding: 3rem 0 5rem; }
.avatar { background: transparent; border: 2px solid var(--acento); color: var(--acento); border-radius: 12px; box-shadow: 0 0 18px rgba(57, 255, 136, 0.3); }
.hero h1 { font-size: 2.1rem; color: var(--acento); }
.hero h1::before { content: "> "; opacity: 0.7; }
.hero h1::after { content: "_"; animation: parpadeo 1.1s steps(1) infinite; }
@keyframes parpadeo { 50% { opacity: 0; } }
.titular { color: var(--texto); }
.metricas li, .tarjeta, .chips li { border-radius: 8px; }
.metricas strong { color: var(--acento); }
.menu a { border-radius: 6px; border: 1px solid var(--borde); background: transparent; color: var(--acento); }
.seccion h2::before { content: "$"; width: auto; height: auto; background: none; color: var(--acento); }
.tarjeta::before { background: var(--acento); height: 2px; }
.titulo-proyecto a { color: var(--acento); }
.chip-lenguaje::before { border-radius: 2px; }
@media (prefers-reduced-motion: reduce) { .hero h1::after { animation: none; } }
"""),
    "aurora": ("Aurora (auroras boreales)", """
:root {
  --fondo: #060a1c; --tarjeta: rgba(255, 255, 255, 0.05); --texto: #eaf0ff; --atenuado: #a3b0d0;
  --borde: rgba(255, 255, 255, 0.12); --acento: #5eead4; --acento-2: #a78bfa; --acento-suave: rgba(94, 234, 212, 0.12);
  --sombra: 0 4px 24px rgba(0, 0, 0, 0.25); --sombra-alta: 0 10px 40px rgba(94, 234, 212, 0.18);
}
body {
  background:
    radial-gradient(900px 500px at 10% -5%, rgba(94, 234, 212, 0.18), transparent 60%),
    radial-gradient(800px 500px at 90% 0%, rgba(167, 139, 250, 0.22), transparent 60%),
    radial-gradient(700px 500px at 50% 100%, rgba(56, 189, 248, 0.12), transparent 60%),
    #060a1c;
  background-attachment: fixed;
}
.banda { background: transparent; padding: 4rem 0 5.5rem; }
.avatar { background: linear-gradient(135deg, #5eead4, #a78bfa); border: 0; color: #07101f; box-shadow: 0 0 40px rgba(94, 234, 212, 0.45); }
.hero h1 { background: linear-gradient(90deg, #5eead4, #a78bfa); -webkit-background-clip: text; background-clip: text; color: transparent; }
.titular { color: var(--texto); }
.metricas li, .tarjeta, .chips li { backdrop-filter: blur(8px); }
.tarjeta::before { background: linear-gradient(90deg, #5eead4, #a78bfa); }
.titulo-proyecto a { color: var(--texto); }
.saltar { color: #07101f; }
"""),
    "flower": ("Flower (floral pastel)", """
:root {
  --fondo: #fff7f9; --tarjeta: #ffffff; --texto: #3b2a3a; --atenuado: #7d6578;
  --borde: #f3d9e3; --acento: #d6427f; --acento-2: #f59ac0; --acento-suave: #fde8f0;
  --sombra: 0 2px 10px rgba(214, 66, 127, 0.08); --sombra-alta: 0 12px 30px rgba(214, 66, 127, 0.18);
}
@media (prefers-color-scheme: dark) {
  :root { --fondo: #fff7f9; --tarjeta: #ffffff; --texto: #3b2a3a; --atenuado: #7d6578; --borde: #f3d9e3; --acento: #d6427f; --acento-2: #f59ac0; --acento-suave: #fde8f0; --sombra: 0 2px 10px rgba(214, 66, 127, 0.08); --sombra-alta: 0 12px 30px rgba(214, 66, 127, 0.18); }
}
body { font-family: Georgia, "Palatino Linotype", "Book Antiqua", serif; }
.banda {
  background:
    radial-gradient(circle at 12% 30%, rgba(255, 255, 255, 0.35) 0 40px, transparent 41px),
    radial-gradient(circle at 88% 70%, rgba(255, 255, 255, 0.3) 0 70px, transparent 71px),
    radial-gradient(circle at 70% 10%, rgba(255, 255, 255, 0.25) 0 28px, transparent 29px),
    linear-gradient(135deg, #f59ac0, #d6427f);
  border-radius: 0 0 48px 48px;
}
.avatar { border-radius: 38% 62% 55% 45% / 50% 40% 60% 50%; }
.hero h1 { font-weight: 700; }
.seccion h2::before { content: "\\273F"; width: auto; height: auto; background: none; color: var(--acento); font-size: 1.2rem; }
.tarjeta { border-radius: 22px; }
.tarjeta::before { background: linear-gradient(90deg, #f59ac0, #d6427f); height: 6px; }
.chips li { background: var(--acento-suave); border-color: transparent; color: #8a2b55; }
.menu a { background: #ffffff; border: 1px solid var(--borde); }
"""),
    "simple": ("Simple (minimalista claro)", """
:root {
  --fondo: #ffffff; --tarjeta: #ffffff; --texto: #111111; --atenuado: #666666;
  --borde: #e6e6e6; --acento: #111111; --acento-2: #111111; --acento-suave: #f2f2f2;
  --sombra: none; --sombra-alta: 0 4px 14px rgba(0, 0, 0, 0.08);
}
@media (prefers-color-scheme: dark) {
  :root { --fondo: #ffffff; --tarjeta: #ffffff; --texto: #111111; --atenuado: #666666; --borde: #e6e6e6; --acento: #111111; --acento-2: #111111; --acento-suave: #f2f2f2; --sombra: none; --sombra-alta: 0 4px 14px rgba(0, 0, 0, 0.08); }
}
.banda { background: #ffffff; color: #111111; padding: 4rem 0 5.5rem; }
.avatar { background: #111111; border: 0; color: #ffffff; box-shadow: none; }
.hero h1 { font-weight: 800; letter-spacing: -0.03em; }
.titular { opacity: 1; color: var(--atenuado); }
.seccion h2::before { display: none; }
.seccion h2 { border-bottom: 1px solid var(--borde); padding-bottom: 0.6rem; }
.tarjeta { border-radius: 4px; box-shadow: none; }
.tarjeta::before { display: none; }
.tarjeta:hover { transform: none; border-color: #111111; }
.chips li { border-radius: 4px; box-shadow: none; }
.menu a { background: transparent; border: 1px solid var(--borde); color: #111111; border-radius: 4px; }
.titulo-proyecto a:hover, .ver a { color: #111111; text-decoration: underline; }
.saltar { color: #ffffff; background: #111111; }
"""),
    "profesional": ("Profesional (currículum)", """
:root {
  --fondo: #eef1f5; --tarjeta: #ffffff; --texto: #1c2733; --atenuado: #5b6877;
  --borde: #d5dbe3; --acento: #1f3a5f; --acento-2: #2f5d8c; --acento-suave: #e4ebf3;
  --sombra: 0 1px 2px rgba(28, 39, 51, 0.08); --sombra-alta: 0 6px 18px rgba(31, 58, 95, 0.15);
}
@media (prefers-color-scheme: dark) {
  :root { --fondo: #eef1f5; --tarjeta: #ffffff; --texto: #1c2733; --atenuado: #5b6877; --borde: #d5dbe3; --acento: #1f3a5f; --acento-2: #2f5d8c; --acento-suave: #e4ebf3; --sombra: 0 1px 2px rgba(28, 39, 51, 0.08); --sombra-alta: 0 6px 18px rgba(31, 58, 95, 0.15); }
}
body { font-family: "Segoe UI", Calibri, "Helvetica Neue", Arial, sans-serif; }
.banda { background: linear-gradient(180deg, #1f3a5f, #28486f); border-bottom: 4px solid #c9a24d; padding: 3rem 0 5rem; }
.avatar { border-radius: 8px; background: #c9a24d; border: 0; color: #1f3a5f; box-shadow: none; }
.hero h1 { font-size: 2.2rem; text-transform: uppercase; letter-spacing: 0.04em; font-weight: 700; }
.metricas li, .tarjeta, .chips li { border-radius: 4px; }
.metricas strong { color: #1f3a5f; }
.menu a { border-radius: 4px; background: #ffffff; border: 1px solid var(--borde); }
.seccion h2 { text-transform: uppercase; letter-spacing: 0.08em; font-size: 1.1rem; border-bottom: 2px solid #c9a24d; padding-bottom: 0.5rem; }
.seccion h2::before { display: none; }
.tarjeta { border-left: 4px solid #1f3a5f; }
.tarjeta::before { display: none; }
.tarjeta:hover { transform: none; }
.chips li { background: var(--acento-suave); border-color: transparent; }
"""),
    "madera": ("Madera (cálido artesanal)", """
:root {
  --fondo: #f3ebdd; --tarjeta: #fffaf0; --texto: #2e1f14; --atenuado: #6f5a47;
  --borde: #dccbb0; --acento: #8a4b21; --acento-2: #5e3216; --acento-suave: #efe0c8;
  --sombra: 0 2px 6px rgba(70, 40, 15, 0.12); --sombra-alta: 0 12px 28px rgba(70, 40, 15, 0.25);
}
@media (prefers-color-scheme: dark) {
  :root { --fondo: #f3ebdd; --tarjeta: #fffaf0; --texto: #2e1f14; --atenuado: #6f5a47; --borde: #dccbb0; --acento: #8a4b21; --acento-2: #5e3216; --acento-suave: #efe0c8; --sombra: 0 2px 6px rgba(70, 40, 15, 0.12); --sombra-alta: 0 12px 28px rgba(70, 40, 15, 0.25); }
}
body { font-family: Georgia, "Palatino Linotype", "Book Antiqua", serif; }
.banda {
  background:
    repeating-linear-gradient(90deg, rgba(0, 0, 0, 0.07) 0 2px, transparent 2px 9px),
    repeating-linear-gradient(90deg, rgba(255, 255, 255, 0.05) 0 1px, transparent 1px 23px),
    linear-gradient(180deg, #8a5a33, #5e3a1d);
  border-bottom: 6px solid #3e2410;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}
.avatar { background: #f3ebdd; color: #5e3216; border: 4px solid #3e2410; }
.hero h1 { letter-spacing: 0; text-shadow: 0 2px 3px rgba(0, 0, 0, 0.35); }
.metricas strong { color: #5e3216; }
.menu a { background: #5e3216; color: #fffaf0; border-radius: 4px; }
.seccion h2::before { background: repeating-linear-gradient(90deg, #8a4b21 0 3px, #5e3216 3px 6px); width: 8px; border-radius: 1px; }
.tarjeta { border-radius: 6px; border: 1px solid var(--borde); border-bottom: 4px solid #8a4b21; }
.tarjeta::before { display: none; }
.chips li { border-radius: 6px; background: var(--acento-suave); }
.titulo-proyecto a { color: #2e1f14; }
.saltar { color: #fffaf0; background: #5e3216; }
"""),
    "tropical": ("Tropical (blanco, rojo y verde)", """
:root {
  --fondo: #ffffff; --tarjeta: #ffffff; --texto: #17301f; --atenuado: #5c7566;
  --borde: #e3efe6; --acento: #e63946; --acento-2: #1b8a4b; --acento-suave: #eaf7ee;
  --sombra: 0 2px 10px rgba(23, 48, 31, 0.07); --sombra-alta: 0 14px 32px rgba(230, 57, 70, 0.16);
}
@media (prefers-color-scheme: dark) {
  :root { --fondo: #ffffff; --tarjeta: #ffffff; --texto: #17301f; --atenuado: #5c7566; --borde: #e3efe6; --acento: #e63946; --acento-2: #1b8a4b; --acento-suave: #eaf7ee; --sombra: 0 2px 10px rgba(23, 48, 31, 0.07); --sombra-alta: 0 14px 32px rgba(230, 57, 70, 0.16); }
}
body {
  background:
    radial-gradient(circle at 0% 0%, rgba(27, 138, 75, 0.10), transparent 38%),
    radial-gradient(circle at 100% 12%, rgba(230, 57, 70, 0.09), transparent 36%),
    #ffffff;
  background-attachment: fixed;
}
.banda {
  background:
    radial-gradient(circle at 85% 20%, rgba(255, 255, 255, 0.22) 0 90px, transparent 91px),
    radial-gradient(circle at 10% 90%, rgba(255, 255, 255, 0.16) 0 60px, transparent 61px),
    linear-gradient(120deg, #e63946 0%, #f26b4f 48%, #1b8a4b 100%);
  color: #ffffff;
  border-radius: 0 0 40px 40px;
  padding: 3.5rem 0 5.5rem;
}
.avatar { background: #ffffff; color: #e63946; border: 4px solid rgba(255, 255, 255, 0.65); }
.hero h1 { letter-spacing: -0.02em; }
.metricas li { border-top: 4px solid #1b8a4b; }
.metricas li:nth-child(2n) { border-top-color: #e63946; }
.metricas strong { color: #e63946; }
.menu a { background: var(--acento-suave); color: #1b8a4b; }
.menu a:hover { background: #1b8a4b; color: #ffffff; }
.seccion h2::before { background: linear-gradient(#e63946 0 50%, #1b8a4b 50% 100%); }
.tarjeta { border-radius: 18px; border-color: var(--borde); }
.tarjeta::before { background: linear-gradient(90deg, #e63946, #f4a261 50%, #1b8a4b); }
.tarjeta:hover { border-color: #e63946; }
.chips li { background: #ffffff; border-color: var(--borde); }
.chips li:nth-child(3n+1) { border-color: rgba(230, 57, 70, 0.45); }
.chips li:nth-child(3n+2) { border-color: rgba(27, 138, 75, 0.45); }
.boton-contacto { color: #1b8a4b; }
.boton-contacto:hover { background: var(--acento-suave); }
.saltar { background: #e63946; color: #ffffff; }
"""),
}

PLANTILLA_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'sha256-<HASH_MAPA>'; base-uri 'none'; form-action 'none'">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer">
<title><TITULO> · Portafolio</title>
<style>
<CSS>
</style>
</head>
<body>
<a class="saltar" href="#contenido">Saltar al contenido</a>
<header class="banda">
<div class="contenedor">
  <div class="hero">
    <div class="avatar" aria-hidden="true"><INICIALES></div>
    <div class="hero-texto">
      <h1><NOMBRE></h1>
      <TITULAR>
    </div>
  </div>
</div>
</header>
<div class="contenedor">
<METRICAS>
<MENU>
<MAPA>
<main id="contenido">
<SECCIONES>
</main>
<footer>
  <p>Portafolio generado con GIPP. El texto fue revisado y aprobado por su autor.</p>
</footer>
</div>
<SCRIPT_MAPA>
</body>
</html>
"""

# Script del mapa lateral. Es fijo (no depende de los datos) y la CSP lo autoriza por
# hash: si cambia una sola letra, el navegador lo bloquea. Solo lee el documento y
# marca el enlace de la sección visible; no escribe HTML ni carga nada externo.
SCRIPT_MAPA = """<script>
(function () {
  var enlaces = document.querySelectorAll('.mapa a[href^="#"]');
  if (!enlaces.length) { return; }
  var secciones = [];
  enlaces.forEach(function (enlace) {
    var seccion = document.getElementById(enlace.getAttribute('href').slice(1));
    if (seccion) { secciones.push(seccion); }
  });
  if (!secciones.length) { return; }
  var pendiente = false;
  function marcar() {
    pendiente = false;
    var linea = window.innerHeight * 0.35;
    var actual = secciones[0];
    var ultima = secciones[secciones.length - 1];
    var fin = window.scrollY + window.innerHeight;
    var total = document.documentElement.scrollHeight;
    if (fin >= total - 4) {
      actual = ultima;
    } else {
      secciones.forEach(function (seccion) {
        if (seccion.getBoundingClientRect().top <= linea) { actual = seccion; }
      });
    }
    enlaces.forEach(function (enlace) {
      enlace.classList.toggle('activo', enlace.getAttribute('href') === '#' + actual.id);
    });
  }
  function programar() {
    if (!pendiente) { pendiente = true; window.requestAnimationFrame(marcar); }
  }
  window.addEventListener('scroll', programar, { passive: true });
  window.addEventListener('resize', programar);
  marcar();
})();
</script>"""


def renderizar_portafolio(usuario: str, nombre: str, titular: str, resumen: str,
                          habilidades: list[str], proyectos: list[dict],
                          plantilla: str = "moderno", contacto: dict | None = None,
                          cv: dict | None = None) -> str:
    """Genera el HTML del portafolio a partir de datos ya validados."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}", usuario):
        raise ValueError("Usuario de GitHub no válido.")
    if plantilla not in TEMAS:
        raise ValueError("Plantilla no válida.")
    nombre_final = nombre.strip() or usuario
    titular = titular.strip()

    iniciales = ""
    for palabra in nombre_final.split():
        if palabra[0].isalpha():
            iniciales += palabra[0].upper()
            if len(iniciales) == 2:
                break
    if not iniciales:
        iniciales = usuario[0].upper()

    secciones = []
    parrafos = []
    for bloque in re.split(r"\n\s*\n", resumen):
        texto = " ".join(bloque.split())
        if texto:
            parrafos.append("<p>" + html.escape(texto) + "</p>")
    if parrafos:
        secciones.append(
            '<section class="seccion sobre-mi" aria-labelledby="sobre-mi">'
            '<h2 id="sobre-mi">Sobre mí</h2>'
            + "".join(parrafos)
            + "</section>"
        )

    chips = [
        "<li>" + html.escape(habilidad.strip()) + "</li>"
        for habilidad in habilidades
        if habilidad.strip()
    ]
    if chips:
        secciones.append(
            '<section class="seccion" aria-labelledby="habilidades">'
            '<h2 id="habilidades">Habilidades y herramientas</h2>'
            '<ul class="chips">' + "".join(chips) + "</ul>"
            "</section>"
        )

    tarjetas = []
    lenguajes: set[str] = set()
    prefijo_url = "https://github.com/" + usuario + "/"
    for proyecto in proyectos:
        nombre_proyecto = html.escape(proyecto.get("name") or "")
        url = proyecto.get("url")
        lenguaje = proyecto.get("language") or None
        descripcion = proyecto.get("description") or None
        if isinstance(url, str) and url.startswith(prefijo_url):
            cabecera = (
                '<h3 class="titulo-proyecto">'
                f'<a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer">'
                f"{nombre_proyecto}</a></h3>"
            )
        else:
            cabecera = '<h3 class="titulo-proyecto">' + nombre_proyecto + "</h3>"
        piezas = [cabecera]
        if lenguaje:
            lenguajes.add(lenguaje.strip().lower())
            piezas.append(
                '<p class="lenguaje"><span class="chip-lenguaje l'
                + str(sum(map(ord, lenguaje.strip().lower())) % 8)
                + '">'
                + html.escape(lenguaje)
                + "</span></p>"
            )
        if descripcion:
            piezas.append(
                '<p class="descripcion">' + html.escape(descripcion) + "</p>"
            )
        if isinstance(url, str) and url.startswith(prefijo_url):
            piezas.append(
                f'<p class="ver"><a href="{html.escape(url)}" target="_blank" '
                'rel="noopener noreferrer">Ver en GitHub &rarr;</a></p>'
            )
        tarjetas.append('<article class="tarjeta">' + "".join(piezas) + "</article>")
    if tarjetas:
        secciones.append(
            '<section class="seccion" aria-labelledby="proyectos">'
            '<h2 id="proyectos">Proyectos</h2>'
            '<div class="grid">' + "".join(tarjetas) + "</div>"
            "</section>"
        )

    datos_contacto, _ = validar_contacto((contacto or {}).get("correo"), (contacto or {}).get("linkedin"))
    botones = [
        '<li><a class="boton-contacto" href="https://github.com/' + html.escape(usuario)
        + '" target="_blank" rel="noopener noreferrer">GitHub</a></li>'
    ]
    if "linkedin" in datos_contacto:
        botones.append(
            '<li><a class="boton-contacto" href="' + html.escape(datos_contacto["linkedin"])
            + '" target="_blank" rel="noopener noreferrer">LinkedIn</a></li>'
        )
    if "correo" in datos_contacto:
        botones.append(
            '<li><a class="boton-contacto" href="mailto:' + html.escape(datos_contacto["correo"])
            + '">Enviar un correo</a></li>'
        )
    tipo_cv = cv_incrustable((cv or {}).get("nombre"), (cv or {}).get("contenido"))
    if tipo_cv:
        datos = base64.b64encode(cv["contenido"]).decode("ascii")
        botones.append(
            '<li><a class="boton-contacto" href="data:' + tipo_cv + ';base64,' + datos
            + '" download="' + html.escape("CV_" + usuario + ".pdf") + '">Descargar CV (PDF)</a></li>'
        )
    if len(botones) > 1:
        detalle = (
            '<p class="contacto-dato">' + html.escape(datos_contacto["correo"]) + "</p>"
            if "correo" in datos_contacto else ""
        )
        secciones.append(
            '<section class="seccion" aria-labelledby="contacto">'
            '<h2 id="contacto">Contacto</h2>'
            '<ul class="chips contacto">' + "".join(botones) + "</ul>" + detalle + "</section>"
        )

    metricas = []
    for cantidad, etiqueta in (
        (len(tarjetas), "proyectos"),
        (len(lenguajes), "lenguajes"),
        (len(chips), "herramientas y habilidades"),
    ):
        if cantidad:
            metricas.append(f"<li><strong>{cantidad}</strong><span>{etiqueta}</span></li>")
    metricas_html = '<ul class="metricas">' + "".join(metricas) + "</ul>" if metricas else ""

    enlaces = [
        (marca, rotulo)
        for marca, rotulo in (
            ('id="sobre-mi"', ("sobre-mi", "Sobre mí")),
            ('id="habilidades"', ("habilidades", "Habilidades")),
            ('id="proyectos"', ("proyectos", "Proyectos")),
            ('id="contacto"', ("contacto", "Contacto")),
        )
        if any(marca in seccion for seccion in secciones)
    ]
    menu_html = ""
    if enlaces:
        menu_html = '<nav aria-label="Secciones"><ul class="menu">' + "".join(
            f'<li><a href="#{ancla}">{rotulo}</a></li>' for _, (ancla, rotulo) in enlaces
        ) + "</ul></nav>"

    mapa_html = ""
    if enlaces:
        mapa_html = (
            '<nav class="mapa" aria-label="Mapa del portafolio">'
            '<p class="mapa-titulo">En esta página</p><ul>'
            + "".join(f'<li><a href="#{ancla}">{rotulo}</a></li>' for _, (ancla, rotulo) in enlaces)
            + "</ul></nav>"
        )
        script_mapa = SCRIPT_MAPA
    else:
        script_mapa = ""
    hash_mapa = base64.b64encode(hashlib.sha256(script_mapa.encode("utf-8")).digest()).decode("ascii")

    nombre_escapado = html.escape(nombre_final)
    titular_html = ""
    if titular:
        titular_html = '<p class="titular">' + html.escape(titular) + "</p>"
    return (
        PLANTILLA_HTML
        .replace("<CSS>", ESTILOS_CSS.replace("@media print", TEMAS[plantilla][1] + "\n@media print"))
        .replace("<TITULO>", nombre_escapado)
        .replace("<NOMBRE>", nombre_escapado)
        .replace("<TITULAR>", titular_html)
        .replace("<INICIALES>", html.escape(iniciales))
        .replace("<METRICAS>", metricas_html)
        .replace("<MENU>", menu_html)
        .replace("<MAPA>", mapa_html)
        .replace("<SCRIPT_MAPA>", script_mapa)
        .replace("<HASH_MAPA>", hash_mapa)
        .replace("<SECCIONES>", "".join(secciones))
    )
