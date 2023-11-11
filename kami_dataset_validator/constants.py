KEY_TRANSLATIONS = {
    'cep': 'cep',
    'logradouro': 'street',
    'complemento': 'complement',
    'bairro': 'district',
    'localidade': 'city',
    'uf': 'state',
}
VALID_UFS = {
    'AC',
    'AL',
    'AP',
    'AM',
    'BA',
    'CE',
    'DF',
    'ES',
    'GO',
    'MA',
    'MT',
    'MS',
    'MG',
    'PA',
    'PB',
    'PR',
    'PE',
    'PI',
    'RJ',
    'RN',
    'RS',
    'RO',
    'RR',
    'SC',
    'SP',
    'SE',
    'TO',
}
CEP_WEBSERVICES = {
    'viacep': {
        'BASE_URL': 'https://viacep.com.br/ws/{}/json/',
        'supports_address': True,
    },
    'brasilaberto': {
        'BASE_URL': 'https://brasilaberto.com/api/v1/zipcode/{}',
        'supports_address': False,
    },
    'opencep': {
        'BASE_URL': 'https://opencep.com/v1/{}',
        'supports_address': False,
    },
    'brasilapi': {
        'BASE_URL': 'https://brasilapi.com.br/api/cep/v2/{}',
        'supports_address': False,
    },
}

CNPJ_WEBSERVICES = {
    'brasilaberto': {'BASE_URL': 'https://brasilaberto.com/api/v1/cnpj/{}'},
    'brasilapi': {'BASE_URL': 'https://brasilapi.com.br/api/cnpj/v1/{}'},
    'receitaws': {'BASE_URL': 'https://receitaws.com.br/v1/cnpj/{}'},
}
