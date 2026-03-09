document.addEventListener('DOMContentLoaded', function () {

    /* ── Live clock ──────────────────────────────────────────────────── */
    const timeEl = document.getElementById('ltime');
    if (timeEl) {
        function tick() {
            timeEl.textContent = new Date().toLocaleTimeString('en-GB', { hour12: false });
        }
        tick();
        setInterval(tick, 1000);
    }

    /* ── Password toggle ─────────────────────────────────────────────── */
    const togglePw = document.getElementById('togglePw');
    const pwInput = document.getElementById('password');
    if (togglePw && pwInput) {
        togglePw.addEventListener('click', function () {
            const isHidden = pwInput.type === 'password';
            pwInput.type = isHidden ? 'text' : 'password';
            togglePw.textContent = isHidden ? '🙈' : '👁';
        });
    }

    /* ── Input focus — lift icon opacity ─────────────────────────────── */
    document.querySelectorAll('.lc-input').forEach(function (input) {
        const ico = input.parentElement.querySelector('.lc-ico');
        if (!ico) return;
        input.addEventListener('focus', function () { ico.style.opacity = '1'; });
        input.addEventListener('blur', function () { ico.style.opacity = input.value ? '1' : '.6'; });
    });

    /* ── Submit button loading state ─────────────────────────────────── */
    const loginForm = document.querySelector('.login-card form');
    const loginBtn = document.querySelector('.lc-btn');
    if (loginForm && loginBtn) {
        loginForm.addEventListener('submit', function () {
            if (document.getElementById('username').value === '' || document.getElementById('password').value === '') return;
            loginBtn.textContent = 'Signing in…';
            loginBtn.style.opacity = '.7';
        });
    }

});
