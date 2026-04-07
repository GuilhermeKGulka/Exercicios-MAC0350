Nesse projeto criaremos um site com uma database de animais brasileiros, com funcionalidade de login e features basicas.

Para rodar o projeto localmente, basta clonar o repositorio e rodar o script setup.py
O script ira solicitar uma chave (seu email) para ser usado no User-Auth na API da wikimedia, apesar de seu uso ser livre

O uso de ferramentas de inteligencia artificial foi feito para: 
-implementar o dropdown no menu lateral do front-end, e a expansao do menu na versao mobile
-importar a database do ctfb (import_ctfb.py) e passa-la para a forma local (em models.py)
-base para a chamada de api para a busca de imagens (img_api.py). Apesar disso o codigo foi altamente alterado para chegar na versao atual, que visa melhor qualidade das imagens, mas mantendo a abrangencia, e minimizando o numero de requisicoes realizadas pelo caching dos dados na database, e respeita copyright ao sempre informar a fonte atribuida a imagem.
-script de setup (setup.py)