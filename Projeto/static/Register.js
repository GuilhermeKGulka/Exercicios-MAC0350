async function enviarCadastro() {
    const senha = document.getElementById('senha').value;
    const checkSenha = document.getElementById('check-senha').value;

    if (senha !== checkSenha) {
        alert("As senhas não coincidem!");
        return;
    }

    const dados = { 
        username: document.getElementById('usuario').value,
        name: null,
        password: senha
    };

    const resposta = await fetch('/createuser', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(dados)
    });

    if (resposta.ok) {
        const resultado = await resposta.json();
        alert("Usuário " + dados.username + " criado!");
    } else {
        alert("Erro ao enviar!");
    }
}