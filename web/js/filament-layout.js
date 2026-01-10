/* ============================================================================
   Filament Layout - Mobile Sidebar Toggle
   =========================================================================== */

document.addEventListener('DOMContentLoaded', function() {
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', function(e) {
      e.preventDefault();
      sidebar.classList.toggle('open');
    });

    // Close sidebar when a link is clicked (mobile)
    sidebar.querySelectorAll('.sidebar__link').forEach(link => {
      link.addEventListener('click', function() {
        if (window.innerWidth <= 768) {
          sidebar.classList.remove('open');
        }
      });
    });

    // Close sidebar on window resize (if resizing from mobile to desktop)
    window.addEventListener('resize', function() {
      if (window.innerWidth > 768) {
        sidebar.classList.remove('open');
      }
    });
  }
});
