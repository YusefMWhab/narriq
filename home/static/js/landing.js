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

    const menuBtn = document.getElementById('mobile-menu-btn');
    const navLinks = document.getElementById('nav-links-menu');

    menuBtn.addEventListener('click', () => {
        navLinks.classList.toggle('active');
    });

    /* اختياري: قفل المنيو لما المستخدم يدوس على أي لينك */
    document.querySelectorAll('.nav-links a').forEach(link => {
        link.addEventListener('click', () => {
            navLinks.classList.remove('active');
        });
    });
});
