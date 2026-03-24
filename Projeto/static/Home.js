async function login() {
    const dados = {
        username: document.getElementById('usuario').value,
        password: document.getElementById('senha').value
    };

    const resposta = await fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(dados)
    });

    if (resposta.redirected) {
        window.location.href = resposta.url;
    } else if (resposta.ok) {
        const resultado = await resposta.json();
        alert("Login bem sucedido!");
    } else {
        alert("Erro ao logar!");
    }
}