document.addEventListener("DOMContentLoaded", () => {
  const toggleButton = document.getElementById("btnToggle");
  const sidebar = document.getElementById("sidebar");

  if (toggleButton && sidebar) {
    toggleButton.addEventListener("click", () => {
      sidebar.classList.toggle("collapsed");
      try {
        localStorage.setItem("sidebarCollapsed", sidebar.classList.contains("collapsed"));
      } catch (error) {
        console.warn("No se pudo guardar el estado del sidebar", error);
      }
    });

    try {
      if (localStorage.getItem("sidebarCollapsed") === "true") {
        sidebar.classList.add("collapsed");
      }
    } catch (error) {
      console.warn("No se pudo leer el estado del sidebar", error);
    }
  }

  document.querySelectorAll("[data-auto-dismiss]").forEach((alert) => {
    setTimeout(() => {
      alert.classList.add("fade");
      setTimeout(() => {
        alert.remove();
      }, 300);
    }, Number(alert.dataset.autoDismiss) || 4500);
  });
});
