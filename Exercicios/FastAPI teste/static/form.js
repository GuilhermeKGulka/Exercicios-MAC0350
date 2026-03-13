async function enviarUsuario() {
    const dados = {
        nome: document.getElementById('nome').value,
        bio: document.getElementById('bio').value
    };

    const resposta = await fetch('/usuarios', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(dados)
    });

    if (resposta.ok) {
        const resultado = await resposta.json();
        alert("Usuário " + resultado.usuario + " criado!");
    } else {
        alert("Erro ao enviar!");
    }
}
    