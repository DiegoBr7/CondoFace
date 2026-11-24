
"use strict";

// ==========================================
// ELEMENTOS E FUNCOES AUXILIARES
// ==========================================

const tabelaMoradores = document.getElementById("tabela-moradores");
const tabelaVisitantes = document.getElementById("tabela-visitantes");

const formularioCadastro = document.getElementById(
    "form-cadastrar-morador"
);

const formularioEdicao = document.getElementById(
    "form-editar-morador"
);

const secaoEdicao = document.getElementById(
    "secao-editar-morador"
);

const mensagemEdicao = document.getElementById(
    "mensagem-edicao"
);

function criarCelula(linha, valor) {
    const celula = linha.insertCell();
    celula.textContent = String(valor ?? "-");
    return celula;
}

function obterTokenCSRF(formulario) {
    return formulario.querySelector(
        'input[name="csrf_token"]'
    ).value;
}


async function lerResposta(resposta) {

    const tipoConteudo = resposta.headers.get(
        "content-type"
    ) || "";

    if (!tipoConteudo.includes("application/json")) {

        if (resposta.redirected) {
            throw new Error(
                "Sua sessão pode ter expirado. " +
                "Faça login novamente."
            );
        }

        throw new Error(
            `A API retornou HTTP ${resposta.status} ` +
            "com uma resposta que não é JSON. " +
            "Verifique a rota no Flask."
        );
    }

    const dados = await resposta.json();

    if (!resposta.ok) {
        throw new Error(
            dados.erro || `Erro HTTP ${resposta.status}`
        );
    }

    return dados;
}



// ==========================================
// DASHBOARD - ESTATISTICAS
// ==========================================

async function carregarDashboard() {

    try {
        const resposta = await fetch("/api/dashboard", {
            credentials: "same-origin"
        });

        const dados = await lerResposta(resposta);

        document.getElementById("moradores").textContent =
            dados.moradores;

        document.getElementById("visitantes").textContent =
            dados.visitantes;

        document.getElementById("permitidos").textContent =
            dados.acessos_permitidos;

        document.getElementById("negados").textContent =
            dados.acessos_negados;

    } catch (erro) {
        console.error("Erro ao carregar dashboard:", erro);
    }
}


// ==========================================
// MORADORES - LISTAGEM
// ==========================================

async function carregarMoradores() {

    const mensagem = document.getElementById(
        "mensagem-moradores"
    );

    tabelaMoradores.replaceChildren();
    mensagem.textContent = "Carregando moradores...";

    try {

        const resposta = await fetch("/api/moradores", {
            credentials: "same-origin"
        });

        const moradores = await lerResposta(resposta);

        if (!Array.isArray(moradores)) {
            throw new Error("Resposta inesperada da API.");
        }

        mensagem.textContent = "";

        if (moradores.length === 0) {
            const linha = tabelaMoradores.insertRow();
            const celula = linha.insertCell();

            celula.colSpan = 7;
            celula.textContent = "Nenhum morador cadastrado.";
            return;
        }

        moradores.forEach((morador) => {

            const linha = tabelaMoradores.insertRow();

            criarCelula(linha, morador.id);
            criarCelula(linha, morador.nome);
            criarCelula(linha, morador.bloco);
            criarCelula(linha, morador.apartamento);

            criarCelula(
                linha,
                morador.ativo ? "Ativo" : "Inativo"
            );

            criarCelula(
                linha,
                morador.biometria_cadastrada
                    ? "Cadastrada"
                    : "Pendente"
            );

            // Coluna de acoes
            const celulaAcoes = linha.insertCell();

            const container = document.createElement("div");
            container.className = "acoes-morador";

            // Botao editar
            const botaoEditar = document.createElement("button");

            botaoEditar.type = "button";
            botaoEditar.className = "btn btn-editar";
            botaoEditar.textContent = "Editar";

            botaoEditar.addEventListener("click", () => {
                abrirEdicao(morador);
            });

            // Botao ativar/desativar
            const botaoStatus = document.createElement("button");

            botaoStatus.type = "button";

            botaoStatus.className = morador.ativo
                ? "btn btn-desativar"
                : "btn btn-ativar";

            botaoStatus.textContent = morador.ativo
                ? "Desativar"
                : "Ativar";

            botaoStatus.addEventListener("click", () => {
                alterarStatusMorador(morador);
            });

            const botaoFace = document.createElement("button");

            botaoFace.type = "button";
            botaoFace.className = "btn btn-primario";
            botaoFace.textContent = "Cadastrar Face";
            botaoFace.disabled = !Boolean(morador.ativo);

            botaoFace.addEventListener("click", () => {
                abrirCadastroFacial("morador", morador);
            });

            const botaoExcluir = document.createElement("button");

            botaoExcluir.type = "button";
            botaoExcluir.className = "btn btn-excluir";
            botaoExcluir.textContent = "Excluir";

            botaoExcluir.addEventListener("click", () => {
                excluirPessoa("morador", morador);
            });

            container.append(
                botaoEditar,
                botaoStatus,
                botaoFace,
                botaoExcluir
            );

            celulaAcoes.appendChild(container);

        });

    } catch (erro) {

        console.error("Erro ao listar moradores:", erro);

        mensagem.textContent =
            "Não foi possível carregar os moradores.";
    }
}


// ==========================================
// MORADORES - CADASTRO
// ==========================================

if (formularioCadastro) {

    formularioCadastro.addEventListener(
        "submit",
        async (evento) => {

            evento.preventDefault();

            const mensagem = document.getElementById(
                "mensagem-cadastro"
            );

            const botao = formularioCadastro.querySelector(
                'button[type="submit"]'
            );

            botao.disabled = true;
            mensagem.textContent = "Cadastrando morador...";

            try {

                const dados = new FormData(formularioCadastro);

                const resposta = await fetch(
                    "/api/moradores",
                    {
                        method: "POST",
                        credentials: "same-origin",
                        body: dados
                    }
                );

                const resultado = await lerResposta(resposta);

                mensagem.textContent = resultado.mensagem;

                formularioCadastro.reset();

                await Promise.all([
                    carregarMoradores(),
                    carregarDashboard()
                ]);

            } catch (erro) {

                console.error("Erro no cadastro:", erro);
                mensagem.textContent = erro.message;

            } finally {
                botao.disabled = false;
            }

        }
    );

}


// ==========================================
// MORADORES - ABRIR EDICAO
// ==========================================

function abrirEdicao(morador) {

    document.getElementById("editar-id").value =
        morador.id;

    document.getElementById("editar-nome").value =
        morador.nome;

    document.getElementById("editar-bloco").value =
        morador.bloco ?? "";

    document.getElementById("editar-apartamento").value =
        morador.apartamento ?? "";

    mensagemEdicao.textContent = "";

    secaoEdicao.hidden = false;

    secaoEdicao.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

    document.getElementById("editar-nome").focus({
        preventScroll: true
    });
}


// ==========================================
// MORADORES - CANCELAR EDICAO
// ==========================================

document.getElementById("cancelar-edicao")
    .addEventListener("click", () => {

        formularioEdicao.reset();
        secaoEdicao.hidden = true;
        mensagemEdicao.textContent = "";

    });


// ==========================================
// MORADORES - SALVAR EDICAO
// ==========================================

formularioEdicao.addEventListener(
    "submit",
    async (evento) => {

        evento.preventDefault();

        const id = document.getElementById(
            "editar-id"
        ).value;

        const botao = formularioEdicao.querySelector(
            'button[type="submit"]'
        );

        botao.disabled = true;
        mensagemEdicao.textContent = "Salvando alterações...";

        try {

            const dados = new FormData(formularioEdicao);

            const resposta = await fetch(
                `/api/moradores/${encodeURIComponent(id)}`,
                {
                    method: "PUT",
                    credentials: "same-origin",
                    body: dados
                }
            );

            const resultado = await lerResposta(resposta);

            formularioEdicao.reset();
            secaoEdicao.hidden = true;

            document.getElementById(
                "mensagem-moradores"
            ).textContent = resultado.mensagem;

            await carregarMoradores();

        } catch (erro) {

            console.error("Erro ao editar:", erro);
            mensagemEdicao.textContent = erro.message;

        } finally {
            botao.disabled = false;
        }

    }
);


// ==========================================
// MORADORES - ATIVAR / DESATIVAR
// ==========================================

async function alterarStatusMorador(morador) {

    const novoStatus = !Boolean(morador.ativo);

    const acao = novoStatus ? "ativar" : "desativar";

    const confirmou = window.confirm(
        `Deseja ${acao} o morador "${morador.nome}"?`
    );

    if (!confirmou) {
        return;
    }

    const mensagem = document.getElementById(
        "mensagem-moradores"
    );

    try {

        const dados = new FormData();

        dados.append(
            "csrf_token",
            obterTokenCSRF(formularioCadastro)
        );

        dados.append(
            "ativo",
            novoStatus ? "1" : "0"
        );

        const resposta = await fetch(
            `/api/moradores/${encodeURIComponent(morador.id)}/status`,
            {
                method: "PATCH",
                credentials: "same-origin",
                body: dados
            }
        );

        const resultado = await lerResposta(resposta);

        await carregarMoradores();

        mensagem.textContent = resultado.mensagem;

    } catch (erro) {

        console.error("Erro ao alterar status:", erro);
        mensagem.textContent = erro.message;

    }
}


// ==========================================
// VISITANTES - LISTAGEM
// ==========================================


async function carregarVisitantes() {

    const tabela = document.getElementById(
        "tabela-visitantes"
    );

    const mensagem = document.getElementById(
        "mensagem-visitantes"
    );

    tabela.replaceChildren();
    mensagem.textContent = "Carregando visitantes...";

    try {
        const resposta = await fetch("/api/visitantes", {
            credentials: "same-origin"
        });

        const visitantes = await lerResposta(resposta);

        if (!Array.isArray(visitantes)) {
            throw new Error("Resposta inválida da API.");
        }

        mensagem.textContent = "";

        if (visitantes.length === 0) {
            const linha = tabela.insertRow();
            const celula = linha.insertCell();

            celula.colSpan = 5;
            celula.textContent = "Nenhum visitante cadastrado.";
            return;
        }

        visitantes.forEach((visitante) => {

            const linha = tabela.insertRow();

            criarCelula(linha, visitante.id);
            criarCelula(linha, visitante.nome);

            criarCelula(
                linha,
                visitante.ativo ? "Ativo" : "Inativo"
            );

            criarCelula(
                linha,
                visitante.biometria_cadastrada
                    ? "Cadastrada"
                    : "Pendente"
            );

            const celulaAcoes = linha.insertCell();

            const container = document.createElement("div");
            container.className = "acoes-morador";

            const botaoEditar = document.createElement("button");
            botaoEditar.type = "button";
            botaoEditar.className = "btn btn-editar";
            botaoEditar.textContent = "Editar";

            botaoEditar.addEventListener("click", () => {
                abrirEdicaoVisitante(visitante);
            });

            const botaoStatus = document.createElement("button");
            botaoStatus.type = "button";

            botaoStatus.className = visitante.ativo
                ? "btn btn-desativar"
                : "btn btn-ativar";

            botaoStatus.textContent = visitante.ativo
                ? "Desativar"
                : "Ativar";

            botaoStatus.addEventListener("click", () => {
                alterarStatusVisitante(visitante);
            });

            const botaoFace = document.createElement("button");

            botaoFace.type = "button";
            botaoFace.className = "btn btn-primario";
            botaoFace.textContent = "Cadastrar Face";
            botaoFace.disabled = !Boolean(visitante.ativo);

            botaoFace.addEventListener("click", () => {
                abrirCadastroFacial("visitante", visitante);
            });

            const botaoExcluir = document.createElement("button");

            botaoExcluir.type = "button";
            botaoExcluir.className = "btn btn-excluir";
            botaoExcluir.textContent = "Excluir";

            botaoExcluir.addEventListener("click", () => {
                excluirPessoa("visitante", visitante);
            });

            container.append(
                botaoEditar,
                botaoStatus,
                botaoFace,
                botaoExcluir
            );
            
            celulaAcoes.appendChild(container);
        });

    } catch (erro) {
        console.error("Erro ao listar visitantes:", erro);
        mensagem.textContent = erro.message;
    }
}


// ==========================================
// ABRIR EDICAO DE VISITANTE
// ==========================================

function abrirEdicaoVisitante(visitante) {

    document.getElementById("editar-visitante-id").value =
        visitante.id;

    document.getElementById("editar-visitante-nome").value =
        visitante.nome;

    document.getElementById("editar-visitante-documento").value =
        visitante.documento ?? "";

    document.getElementById("editar-visitante-telefone").value =
        visitante.telefone ?? "";

    const secao = document.getElementById(
        "secao-editar-visitante"
    );

    document.getElementById(
        "mensagem-edicao-visitante"
    ).textContent = "";

    secao.hidden = false;

    secao.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}


// ==========================================
// SALVAR EDICAO DE VISITANTE
// ==========================================

document.getElementById("form-editar-visitante")
    .addEventListener("submit", async (evento) => {

        evento.preventDefault();

        const formulario = evento.currentTarget;

        const id = document.getElementById(
            "editar-visitante-id"
        ).value;

        const mensagem = document.getElementById(
            "mensagem-edicao-visitante"
        );

        const botao = formulario.querySelector(
            'button[type="submit"]'
        );

        botao.disabled = true;
        mensagem.textContent = "Salvando alterações...";

        try {
            const resposta = await fetch(
                `/api/visitantes/${encodeURIComponent(id)}`,
                {
                    method: "PUT",
                    credentials: "same-origin",
                    body: new FormData(formulario)
                }
            );

            const resultado = await lerResposta(resposta);

            await carregarVisitantes();

            document.getElementById(
                "mensagem-visitantes"
            ).textContent = resultado.mensagem;

            formulario.reset();

            document.getElementById(
                "secao-editar-visitante"
            ).hidden = true;

        } catch (erro) {
            console.error("Erro ao editar visitante:", erro);
            mensagem.textContent = erro.message;

        } finally {
            botao.disabled = false;
        }
    });


// ==========================================
// CANCELAR EDICAO DE VISITANTE
// ==========================================

document.getElementById("cancelar-edicao-visitante")
    .addEventListener("click", () => {

        document.getElementById(
            "form-editar-visitante"
        ).reset();

        document.getElementById(
            "secao-editar-visitante"
        ).hidden = true;

    });


// ==========================================
// ATIVAR / DESATIVAR VISITANTE
// ==========================================

async function alterarStatusVisitante(visitante) {

    const novoStatus = !Boolean(visitante.ativo);
    const acao = novoStatus ? "ativar" : "desativar";

    if (!window.confirm(
        `Deseja ${acao} o visitante "${visitante.nome}"?`
    )) {
        return;
    }

    const mensagem = document.getElementById(
        "mensagem-visitantes"
    );

    try {
        const dados = new FormData();

        dados.append(
            "csrf_token",
            obterTokenCSRF(
                document.getElementById(
                    "form-cadastrar-visitante"
                )
            )
        );

        dados.append("ativo", novoStatus ? "1" : "0");

        const resposta = await fetch(
            `/api/visitantes/${encodeURIComponent(visitante.id)}/status`,
            {
                method: "PATCH",
                credentials: "same-origin",
                body: dados
            }
        );

        const resultado = await lerResposta(resposta);

        await carregarVisitantes();

        mensagem.textContent = resultado.mensagem;

    } catch (erro) {
        console.error("Erro ao alterar status:", erro);
        mensagem.textContent = erro.message;
    }
}



// ==========================================
// INICIALIZACAO
// ==========================================

document.getElementById("atualizar-moradores")
    .addEventListener("click", carregarMoradores);

document.getElementById("atualizar-visitantes")
    .addEventListener("click", carregarVisitantes);

carregarDashboard();
carregarMoradores();
carregarVisitantes();



// ==========================================
// VISITANTES - CADASTRO
// ==========================================

const formularioVisitante = document.getElementById(
    "form-cadastrar-visitante"
);

if (formularioVisitante) {

    formularioVisitante.addEventListener(
        "submit",
        async (evento) => {

            evento.preventDefault();

            const mensagem = document.getElementById(
                "mensagem-cadastro-visitante"
            );

            const botao = formularioVisitante.querySelector(
                'button[type="submit"]'
            );

            botao.disabled = true;
            mensagem.textContent = "Cadastrando visitante...";

            try {

                const dados = new FormData(formularioVisitante);

                const resposta = await fetch(
                    "/api/visitantes",
                    {
                        method: "POST",
                        credentials: "same-origin",
                        body: dados
                    }
                );

                const resultado = await lerResposta(resposta);

                formularioVisitante.reset();

                mensagem.textContent = resultado.mensagem;

                await Promise.all([
                    carregarVisitantes(),
                    carregarDashboard()
                ]);

            } catch (erro) {

                console.error(
                    "Erro ao cadastrar visitante:",
                    erro
                );

                mensagem.textContent = erro.message;

            } finally {

                botao.disabled = false;

            }

        }
    );

}



"use strict";

// ==========================================
// CADASTRO FACIAL - CAMERA DO NAVEGADOR
// ==========================================

const secaoBiometria = document.getElementById(
    "secao-biometria"
);

const videoBiometria = document.getElementById(
    "biometria-video"
);

const mensagemBiometria = document.getElementById(
    "biometria-mensagem"
);

const botaoIniciarBiometria = document.getElementById(
    "biometria-iniciar"
);

const barraBiometria = document.getElementById(
    "biometria-barra"
);

const progressoBiometria = document.getElementById(
    "biometria-progresso"
);

let pessoaBiometria = null;
let streamBiometria = null;
let capturandoBiometria = false;
let cancelarBiometria = false;
let requisicaoBiometria = null;


// ==========================================
// ATUALIZAR PROGRESSO
// ==========================================

function atualizarProgressoBiometria(quantidade) {

    barraBiometria.value = quantidade;

    progressoBiometria.textContent =
        `Imagens enviadas: ${quantidade}/30`;
}


// ==========================================
// ENCERRAR CAMERA
// ==========================================

function encerrarCameraBiometria() {

    if (streamBiometria) {

        streamBiometria.getTracks().forEach(
            track => track.stop()
        );

        streamBiometria = null;
    }

    videoBiometria.srcObject = null;
}


// ==========================================
// ABRIR CADASTRO FACIAL
// ==========================================

async function abrirCadastroFacial(tipo, pessoa) {

    if (capturandoBiometria) {
        return;
    }

    encerrarCameraBiometria();

    pessoaBiometria = {
        tipo,
        id: pessoa.id,
        nome: pessoa.nome
    };

    atualizarProgressoBiometria(0);

    mensagemBiometria.textContent =
        "Solicitando acesso à câmera...";

    document.getElementById(
        "biometria-pessoa"
    ).textContent =
        `${tipo === "morador" ? "Morador" : "Visitante"}: ` +
        `${pessoa.nome} (ID ${pessoa.id})`;

    secaoBiometria.hidden = false;

    secaoBiometria.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

    botaoIniciarBiometria.disabled = true;

    try {

        if (!navigator.mediaDevices?.getUserMedia) {

            throw new Error(
                "Câmera indisponível. " +
                "Use localhost ou HTTPS."
            );
        }

        streamBiometria =
            await navigator.mediaDevices.getUserMedia({

                audio: false,

                video: {
                    facingMode: "user",
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            });

        if (secaoBiometria.hidden) {
            encerrarCameraBiometria();
            return;
        }

        videoBiometria.srcObject = streamBiometria;

        await videoBiometria.play();

        mensagemBiometria.textContent =
            "Câmera pronta. Posicione apenas " +
            "uma pessoa diante dela.";

        botaoIniciarBiometria.disabled = false;

    } catch (erro) {

        encerrarCameraBiometria();

        mensagemBiometria.textContent =
            `Não foi possível abrir a câmera: ${erro.message}`;
    }
}


// ==========================================
// AGUARDAR ENTRE CAPTURAS
// ==========================================

function aguardarBiometria(ms) {

    return new Promise(resolve => {
        setTimeout(resolve, ms);
    });
}


// ==========================================
// CAPTURAR IMAGEM DA WEBCAM
// ==========================================

async function criarFotoBiometria() {

    if (
        !videoBiometria.videoWidth ||
        !videoBiometria.videoHeight
    ) {
        throw new Error(
            "A câmera ainda não está pronta."
        );
    }

    const canvas = document.createElement("canvas");

    canvas.width = videoBiometria.videoWidth;
    canvas.height = videoBiometria.videoHeight;

    const contexto = canvas.getContext("2d");

    if (!contexto) {
        throw new Error(
            "Não foi possível inicializar a captura."
        );
    }

    contexto.drawImage(
        videoBiometria,
        0,
        0,
        canvas.width,
        canvas.height
    );

    const blob = await new Promise(resolve => {

        canvas.toBlob(
            resolve,
            "image/jpeg",
            0.85
        );
    });

    if (!blob) {
        throw new Error(
            "Não foi possível capturar a imagem."
        );
    }

    return blob;
}


// ==========================================
// INICIAR CAPTURA AUTOMATICA
// ==========================================

botaoIniciarBiometria.addEventListener(
    "click",
    async () => {

        if (
            capturandoBiometria ||
            !pessoaBiometria ||
            !streamBiometria
        ) {
            return;
        }

        capturandoBiometria = true;
        cancelarBiometria = false;

        botaoIniciarBiometria.disabled = true;

        let quantidade = 0;
        let tentativas = 0;

        const maxTentativas = 90;

        const pessoa = {
            ...pessoaBiometria
        };

        try {

            while (
                quantidade < 30 &&
                tentativas < maxTentativas &&
                !cancelarBiometria
            ) {

                tentativas++;

                const imagem = await criarFotoBiometria();

                if (cancelarBiometria) {
                    break;
                }

                const dados = new FormData();

                dados.append(
                    "csrf_token",
                    document.getElementById(
                        "biometria-csrf"
                    ).value
                );

                dados.append(
                    "tipo",
                    pessoa.tipo
                );

                dados.append(
                    "pessoa_id",
                    String(pessoa.id)
                );

                dados.append(
                    "imagem",
                    imagem,
                    "captura.jpg"
                );

                requisicaoBiometria =
                    new AbortController();

                try {

                    const resposta = await fetch(
                        "/api/biometria/cadastrar",
                        {
                            method: "POST",
                            credentials: "same-origin",
                            body: dados,
                            signal: requisicaoBiometria.signal
                        }
                    );

                    const resultado =
                        await lerResposta(resposta);

                    quantidade = resultado.quantidade;

                    atualizarProgressoBiometria(
                        quantidade
                    );

                    mensagemBiometria.textContent =
                        `Capturando ${pessoa.nome}: ` +
                        `${quantidade}/30`;

                } catch (erro) {

                    if (
                        cancelarBiometria ||
                        erro.name === "AbortError"
                    ) {
                        break;
                    }

                    const erroDeteccao =
                        /Nenhum rosto detectado|Mais de um rosto detectado|Não foi possível processar o rosto/i
                            .test(erro.message);

                    if (erroDeteccao) {

                        mensagemBiometria.textContent =
                            `${erro.message} ` +
                            "Ajuste a posição.";

                    } else {

                        throw erro;
                    }

                } finally {

                    requisicaoBiometria = null;
                }

                if (
                    !cancelarBiometria &&
                    quantidade < 30
                ) {

                    await aguardarBiometria(500);
                }
            }

            if (!cancelarBiometria) {

                mensagemBiometria.textContent =
                    quantidade === 30
                        ? "30 imagens salvas. " +
                        "Próximo passo: treinar o LBPH."
                        : "Captura interrompida. " +
                        "Verifique a iluminação.";
            }

        } catch (erro) {

            mensagemBiometria.textContent =
                erro.message;

            console.error(
                "Erro no cadastro facial:",
                erro
            );

        } finally {

            capturandoBiometria = false;

            encerrarCameraBiometria();

            botaoIniciarBiometria.disabled = true;

            await Promise.allSettled([
                carregarMoradores(),
                carregarVisitantes()
            ]);
        }
    }
);


// ==========================================
// CANCELAR CADASTRO FACIAL
// ==========================================

document.getElementById(
    "biometria-cancelar"
).addEventListener("click", () => {

    cancelarBiometria = true;

    requisicaoBiometria?.abort();

    encerrarCameraBiometria();

    secaoBiometria.hidden = true;

    botaoIniciarBiometria.disabled = true;
});



async function carregarHistorico() {
    const tabela = document.getElementById("tabela-historico");
    const mensagem = document.getElementById("mensagem-historico");

    if (!tabela || !mensagem) return;

    tabela.replaceChildren();
    mensagem.textContent = "Carregando histórico...";

    try {
        const resposta = await fetch("/api/historico", {
            credentials: "same-origin"
        });

        const historico = await lerResposta(resposta);

        if (!Array.isArray(historico)) {
            throw new Error("Resposta inesperada da API.");
        }

        mensagem.textContent = "";

        if (historico.length === 0) {
            mensagem.textContent = "Nenhum acesso registrado.";
            return;
        }


        historico.forEach((acesso) => {
            const linha = tabela.insertRow();

            const dataFormatada = acesso.data_hora
                ? new Date(acesso.data_hora).toLocaleString("pt-BR", {
                    timeZone: "America/Sao_Paulo"
                })
                : "Não informada";

            criarCelula(linha, acesso.id);
            criarCelula(linha, acesso.nome_pessoa);
            criarCelula(linha, acesso.tipo_pessoa);
            criarCelula(linha, dataFormatada);
            criarCelula(linha, acesso.resultado);
            criarCelula(linha, acesso.motivo);
        });


    } catch (erro) {
        console.error("Erro ao carregar histórico:", erro);
        mensagem.textContent = "Erro ao consultar histórico.";
    }
}

const botaoAtualizarHistorico =
    document.getElementById("atualizar-historico");

if (botaoAtualizarHistorico) {
    botaoAtualizarHistorico.addEventListener(
        "click",
        carregarHistorico
    );
}

carregarHistorico();


// ==========================================
// EXCLUIR MORADOR OU VISITANTE
// ==========================================

async function excluirPessoa(tipo, pessoa) {

    const confirmou = window.confirm(
        `Deseja realmente excluir o ${tipo} "${pessoa.nome}"?`
    );

    if (!confirmou) {
        return;
    }

    const tabela = tipo === "morador"
        ? "moradores"
        : "visitantes";

    const formulario = tipo === "morador"
        ? formularioCadastro
        : document.getElementById("form-cadastrar-visitante");

    const mensagem = document.getElementById(
        `mensagem-${tabela}`
    );

    try {

        const dados = new FormData();

        dados.append(
            "csrf_token",
            obterTokenCSRF(formulario)
        );

        const resposta = await fetch(
            `/api/${tabela}/${encodeURIComponent(pessoa.id)}`,
            {
                method: "DELETE",
                credentials: "same-origin",
                body: dados
            }
        );

        const resultado = await lerResposta(resposta);

        await Promise.all([
            carregarMoradores(),
            carregarVisitantes(),
            carregarDashboard()
        ]);

        mensagem.textContent = resultado.mensagem;

    } catch (erro) {

        console.error("Erro ao excluir:", erro);
        mensagem.textContent = erro.message;

    }
}

"use strict";


