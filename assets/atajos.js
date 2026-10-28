// Atajos del laboratorio: espacio reproduce o pausa, ← y → cambian de paso.
// También mantiene a la vista la columna actual de la tabla y del bus.
(function () {
  "use strict";
  var TECLAS = { " ": "boton-reproducir", ArrowLeft: "boton-anterior", ArrowRight: "boton-siguiente" };
  var EDITABLES = /^(INPUT|TEXTAREA|SELECT)$/;

  document.addEventListener("keydown", function (evento) {
    if (evento.altKey || evento.ctrlKey || evento.metaKey) return;
    var destino = evento.target;
    if (destino && (EDITABLES.test(destino.tagName) || destino.isContentEditable)) return;
    var id = TECLAS[evento.key];
    if (!id) return;
    var boton = document.getElementById(id);
    if (!boton || boton.disabled) return;
    if (evento.key === " " && destino && destino.tagName === "BUTTON" && destino.id !== id) return;
    evento.preventDefault();
    boton.click();
  });

  function centrar(contenedor, elemento) {
    if (!contenedor || !elemento) return;
    var izquierda = elemento.offsetLeft - contenedor.clientWidth / 2 + elemento.offsetWidth / 2;
    contenedor.scrollTo({ left: Math.max(0, izquierda), behavior: "auto" });
  }

  var pendiente = false;
  function seguir() {
    if (pendiente) return;
    pendiente = true;
    requestAnimationFrame(function () {
      pendiente = false;
      centrar(document.querySelector(".bus-cinta"), document.querySelector('.ref[data-estado="actual"]'));
      document.querySelectorAll(".tablas-cinta").forEach(function (cinta) {
        centrar(cinta, cinta.querySelector('.tp-ref[data-col="actual"]'));
      });
    });
  }

  var observador = new MutationObserver(seguir);
  function iniciar() {
    observador.observe(document.body, { subtree: true, attributes: true, attributeFilter: ["data-estado", "data-col"] });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar);
  else iniciar();
})();
