async function enviarCadastro() {
    const senha = document.getElementById('senha').value;
    const checkSenha = document.getElementById('check-senha').value;

    if (senha === "") {
        alert("A senha não pode ser vazia!");
        return;
    }

    if (senha !== checkSenha) {
        alert("As senhas não coincidem!");
        return;
    }

    const dados = { 
        username: document.getElementById('usuario').value,
        name: document.getElementById('usuario').value,
        password: senha
    };

    const resposta = await fetch('/createuser', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(dados)
    });

    if (resposta.redirected) {
        window.location.href = resposta.url;
    } else {
        const resultado = await resposta.json();
        alert(resultado.error);
    }
}