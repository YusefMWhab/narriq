function animateOut(el, direction) {
    return new Promise(resolve => {
        el.style.transition = 'opacity 0.22s ease, transform 0.22s ease';
        el.style.opacity = '0';
        el.style.transform = direction === 'left'
            ? 'translateX(-18px)'
            : 'translateX(18px)';

        setTimeout(() => {
            el.style.display = 'none';
            el.style.transition = '';
            el.style.opacity   = '';
            el.style.transform = '';
            resolve();
        }, 220);
    });
}

function animateIn(el, direction) {
    const startX = direction === 'left' ? '18px' : '-18px';
    el.style.display   = 'block';
    el.style.opacity   = '0';
    el.style.transform = `translateX(${startX})`;

    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            el.style.transition = 'opacity 0.28s ease, transform 0.28s ease';
            el.style.opacity    = '1';
            el.style.transform  = 'translateX(0)';

            setTimeout(() => {
                el.style.transition = '';
            }, 280);
        });
    });
}

function switchTo(section) {
    const wrapper    = document.getElementById('auth-wrapper');
    const loginForm  = document.getElementById('login-section');
    const signupForm = document.getElementById('signup-section');
    const loginInfo  = document.getElementById('login-info');
    const signupInfo = document.getElementById('signup-info');

    if (section === 'signup') {
        // الفورم والإنفو بيطلعوا لليسار، والجدد بييجوا من اليمين
        Promise.all([
            animateOut(loginForm, 'left'),
            animateOut(loginInfo, 'left'),
        ]).then(() => {
            wrapper.style.flexDirection = 'row-reverse';
            animateIn(signupForm, 'right');
            animateIn(signupInfo, 'right');
        });

    } else {
        // العكس — بيطلعوا لليمين والجدد بييجوا من الشمال
        Promise.all([
            animateOut(signupForm, 'right'),
            animateOut(signupInfo, 'right'),
        ]).then(() => {
            wrapper.style.flexDirection = 'row';
            animateIn(loginForm, 'left');
            animateIn(loginInfo, 'left');
        });
    }
}

if (typeof activeTabFromServer !== 'undefined' && activeTabFromServer === 'signup') {
    const wrapper    = document.getElementById('auth-wrapper');
    const loginForm  = document.getElementById('login-section');
    const signupForm = document.getElementById('signup-section');
    const loginInfo  = document.getElementById('login-info');
    const signupInfo = document.getElementById('signup-info');

    loginForm.style.display  = 'none';
    signupForm.style.display = 'block';
    loginInfo.style.display  = 'none';
    signupInfo.style.display = 'block';
    wrapper.style.flexDirection = 'row-reverse';
}



document.addEventListener('DOMContentLoaded', function() {
        
        const messageContainer = document.getElementById('messages-container');
        
        if (messageContainer) {
            
            setTimeout(function() {
                
                messageContainer.style.transition = "opacity 0.5s ease";
                messageContainer.style.opacity = "0";
                
                
                setTimeout(function() {
                    messageContainer.remove();
                }, 500); 
            }, 3000); 
        }
    });