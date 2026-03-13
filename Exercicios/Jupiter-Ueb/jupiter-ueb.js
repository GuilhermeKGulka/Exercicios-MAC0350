document.addEventListener('DOMContentLoaded', function() {
    const menuItems = document.querySelectorAll('.menu-item');
    const botaoExpandir = document.querySelector('.botao-expandir');
    const container = document.querySelector('.container');
    const secaoEsquerda = document.querySelector('.secao-esquerda');

    function isMobile() {
        return window.innerWidth <= 768;
    }

    function fecharTodosSubmenus() {
        document.querySelectorAll('.submenu').forEach(submenu => {
            submenu.style.maxHeight = '0';
            submenu.style.opacity = '0';
        });
    }

    // Controle do botão expandir
    if (botaoExpandir && container) {
        botaoExpandir.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            container.classList.toggle('expandido');
            
            if (container.classList.contains('expandido')) {
                fecharTodosSubmenus();
                // Previne scroll do body quando menu está aberto
                document.body.style.overflow = 'hidden';
            } else {
                document.body.style.overflow = '';
            }
        });
    }

    // Fecha o menu ao clicar fora (apenas mobile)
    document.addEventListener('click', function(event) {
        if (isMobile() && container && container.classList.contains('expandido')) {
            if (secaoEsquerda && !secaoEsquerda.contains(event.target) && 
                botaoExpandir && !botaoExpandir.contains(event.target)) {
                container.classList.remove('expandido');
                document.body.style.overflow = '';
            }
        }
    });

    // Configurar menu para mobile (click em vez de hover)
    function configurarMenuMobile() {
        if (isMobile()) {
            // Remove comportamento hover e adiciona click
            document.querySelectorAll('.menu-botao').forEach(botao => {
                // Remove eventos antigos clonando
                const novoBotao = botao.cloneNode(true);
                botao.parentNode.replaceChild(novoBotao, botao);
            });
            
            // Adiciona novos eventos
            document.querySelectorAll('.menu-botao').forEach(botao => {
                botao.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const submenu = this.nextElementSibling;
                    
                    if (submenu && submenu.classList.contains('submenu')) {
                        const isOpen = submenu.style.maxHeight && submenu.style.maxHeight !== '0px';
                        
                        // Fecha todos os outros
                        document.querySelectorAll('.submenu').forEach(s => {
                            if (s !== submenu) {
                                s.style.maxHeight = '0';
                                s.style.opacity = '0';
                            }
                        });
                        
                        // Alterna o clicado
                        submenu.style.maxHeight = isOpen ? '0' : '200px';
                        submenu.style.opacity = isOpen ? '0' : '1';
                    }
                });
            });
        } else {
            // Modo desktop: remove estilos inline
            document.querySelectorAll('.submenu').forEach(submenu => {
                submenu.style.maxHeight = '';
                submenu.style.opacity = '';
            });
            document.body.style.overflow = '';
        }
    }

    // Inicializa
    configurarMenuMobile();

    // Reconfigura ao redimensionar
    window.addEventListener('resize', function() {
        configurarMenuMobile();
        if (!isMobile() && container && container.classList.contains('expandido')) {
            container.classList.remove('expandido');
            document.body.style.overflow = '';
        }
    });

    // Fecha menu com botão voltar do Android (opcional)
    window.addEventListener('popstate', function() {
        if (container && container.classList.contains('expandido')) {
            container.classList.remove('expandido');
            document.body.style.overflow = '';
        }
    });
});