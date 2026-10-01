class DominioError(Exception):
    """Exceção base para regras de negócio do domínio."""
    def __init__(self, mensagem: str):
        self.mensagem = mensagem
        super().__init__(mensagem)


class RegistroJaExisteError(DominioError):
    """Lançada ao tentar cadastrar registro com dado único já existente (ex: CPF, matrícula, email)."""
    pass


class EntidadeNaoEncontradaError(DominioError):
    """Lançada quando uma entidade buscada por ID ou chave não é encontrada."""
    pass


class CredenciaisInvalidasError(DominioError):
    """Lançada quando autenticação falha por login/senha incorretos ou usuário inativo."""
    pass
