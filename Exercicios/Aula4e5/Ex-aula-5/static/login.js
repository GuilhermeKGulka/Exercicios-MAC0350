async function login() {
    const dados = {
        nome: document.getElementById('nome').value,
        senha: document.getElementById('senha').value
    };

    const resposta = await fetch('/loginn', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(dados)
    });

    if (resposta.ok) {
        const resultado = await resposta.json();
        alert("logado");
    } else {
        alert("Erro ao logar");
    }
}