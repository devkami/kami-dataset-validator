from validate_docbr import CPF, CNPJ

def validate_cpf(cpf):
    cpf_validator = CPF()
    return cpf_validator.validate(cpf)

def validate_cnpj(cnpj):
    cnpj_validator = CNPJ()
    return cnpj_validator.validate(cnpj)