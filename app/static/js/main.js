document.addEventListener('DOMContentLoaded', function() {
    // 1. Auto-dismiss flash alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            if (alert && alert.parentNode) {
                var bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                bsAlert.close();
            }
        }, 5000);
    });

    // 2. Sidebar toggle for mobile
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarClose = document.getElementById('sidebarClose');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    function openSidebar() {
        if (sidebar) sidebar.classList.add('show');
        if (sidebarOverlay) sidebarOverlay.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        if (sidebar) sidebar.classList.remove('show');
        if (sidebarOverlay) sidebarOverlay.classList.remove('show');
        document.body.style.overflow = '';
    }

    if (sidebarToggle) sidebarToggle.addEventListener('click', openSidebar);
    if (sidebarClose) sidebarClose.addEventListener('click', closeSidebar);
    if (sidebarOverlay) sidebarOverlay.addEventListener('click', closeSidebar);

    // 3. Confirm dialogs
    document.querySelectorAll('[data-confirm]').forEach(function(el) {
        el.addEventListener('click', function(e) {
            if (!confirm(el.getAttribute('data-confirm'))) {
                e.preventDefault();
            }
        });
    });

    // Also handle forms with onsubmit confirm
    document.querySelectorAll('form[data-confirm]').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!confirm(form.getAttribute('data-confirm'))) {
                e.preventDefault();
            }
        });
    });

    // 4. CSRF token helper
    window.getCSRFToken = function() {
        var meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    };

    // 5. Active sidebar link highlighting
    const currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar-nav .nav-link').forEach(function(link) {
        const href = link.getAttribute('href');
        if (href === currentPath || (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('active');
        }
    });

    // 6. Tooltip initialization
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function(el) {
        new bootstrap.Tooltip(el);
    });

    // 7. Form select styling
    document.querySelectorAll('.form-select').forEach(function(select) {
        if (!select.value) select.classList.add('text-muted');
        select.addEventListener('change', function() {
            this.classList.toggle('text-muted', !this.value);
        });
    });

    // 8. Close sidebar on window resize to desktop
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 992) {
            closeSidebar();
        }
    });

    // 9. Real-time Notification Polling & Live Toast
    const navNotifBadge = document.getElementById('navNotifBadge');
    const dropdownNotifBadge = document.getElementById('dropdownNotifBadge');
    const toastEl = document.getElementById('liveNotifToast');
    const toastTitle = document.getElementById('liveNotifToastTitle');
    const toastMsg = document.getElementById('liveNotifToastMessage');
    const toastLink = document.getElementById('liveNotifToastLink');

    if (navNotifBadge) {
        let lastKnownLatestId = null;
        let isFirstCheck = true;

        function updateNotifBadges(count) {
            if (count > 0) {
                const text = count > 99 ? '99+' : count;
                if (navNotifBadge) {
                    navNotifBadge.textContent = text;
                    navNotifBadge.classList.remove('d-none');
                }
                if (dropdownNotifBadge) {
                    dropdownNotifBadge.textContent = text;
                    dropdownNotifBadge.classList.remove('d-none');
                }
            } else {
                if (navNotifBadge) navNotifBadge.classList.add('d-none');
                if (dropdownNotifBadge) dropdownNotifBadge.classList.add('d-none');
            }
        }

        function checkNotifications() {
            fetch('/api/notifikasi/status')
                .then(function(res) {
                    if (!res.ok) throw new Error('Not logged in or network error');
                    return res.json();
                })
                .then(function(data) {
                    updateNotifBadges(data.unread_count);

                    if (data.latest) {
                        const newId = data.latest.id;
                        if (!isFirstCheck && lastKnownLatestId !== null && newId > lastKnownLatestId) {
                            // New notification arrived in real time!
                            if (toastEl && toastTitle && toastMsg) {
                                toastTitle.textContent = data.latest.judul;
                                toastMsg.textContent = data.latest.pesan;
                                if (toastLink && data.latest.link) {
                                    toastLink.setAttribute('href', '/notifikasi/baca/' + newId);
                                }
                                const bsToast = bootstrap.Toast.getOrCreateInstance(toastEl, { delay: 6000 });
                                bsToast.show();
                            }
                            // If on /notifikasi page, automatically refresh content so the list updates live!
                            if (window.location.pathname === '/notifikasi') {
                                setTimeout(function() {
                                    window.location.reload();
                                }, 1500);
                            }
                        }
                        lastKnownLatestId = newId;
                    }
                    isFirstCheck = false;
                })
                .catch(function(err) {
                    // Silently ignore network / auth errors during polling
                });
        }

        // Run check initially after 2 seconds, then every 6 seconds
        setTimeout(checkNotifications, 2000);
        setInterval(checkNotifications, 6000);
    }

    // 10. Prevent double submission on submit buttons
    document.querySelectorAll('form').forEach(function(form) {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !form.hasAttribute('data-no-disable')) {
                setTimeout(function() {
                    submitBtn.disabled = true;
                }, 50);
            }
        });
    });
});
