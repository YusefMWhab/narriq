document.addEventListener("DOMContentLoaded", function () {
    const alerts = document.querySelectorAll(".alert");

    alerts.forEach((alert) => {
        // show animation
        setTimeout(() => {
            alert.classList.add("show");
        }, 50);

        // hide after 4 seconds
        setTimeout(() => {
            alert.classList.remove("show");

            // optional: remove from DOM after fade out
            setTimeout(() => {
                alert.remove();
            }, 300);
        }, 4000);
    });
});
