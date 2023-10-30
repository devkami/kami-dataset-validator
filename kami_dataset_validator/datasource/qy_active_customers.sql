SELECT
  DISTINCTROW IFNULL(
    CAST(`cliente`.`cod_cliente` AS CHAR charset utf8mb4),
    '0'
  ) AS `cod_cliente`,
  IFNULL(
    CAST(`cliente`.`cpf` AS CHAR charset utf8mb4),
    '0'
  ) AS `cpf`,
  IFNULL(
    CAST(`cliente`.`cnpj` AS CHAR charset utf8mb4),
    '0'
  ) AS `cnpj`,  
  IFNULL(
    CAST(`cliente`.`nome_cliente` AS CHAR charset utf8mb4),
    '0'
  ) AS `nome_cliente`,
  IFNULL(
    CAST(`cliente`.`razao_social` AS CHAR charset utf8mb4),
    '0'
  ) AS `razao_social`,
  IFNULL(
    CAST(`cliente`.`tp_cliente` AS CHAR charset utf8mb4),
    '0'
  ) AS `tp_cliente`,
  IFNULL(
    CAST(`cliente`.`insc_municipal` AS CHAR charset utf8mb4),
    '0'
  ) AS `insc_municipal`,
    IFNULL(
    CAST(`cliente`.`insc_estadual` AS CHAR charset utf8mb4),
    '0'
  ) AS `insc_estadual`,
  IFNULL(
    CAST(
      `ramo_atividade`.`desc_abrev` AS CHAR charset utf8mb4
    ),
    '0'
  ) AS `ramo_atividade`,
  IFNULL(
    CAST(`cliente`.`email_certificado` AS CHAR charset utf8mb4),
    '0'
  ) AS `email_certificado`,
  IFNULL(
    CAST(`cliente`.`email_cobranca` AS CHAR charset utf8mb4),
    '0'
  ) AS `email_cobranca`,
  IFNULL(
    CAST(`cliente`.`email_ecommerce` AS CHAR charset utf8mb4),
    '0'
  ) AS `email_ecommerce`,
  IFNULL(
    CAST(`cliente`.`email_nfe` AS CHAR charset utf8mb4),
    '0'
  ) AS `email_nfe`,
  IFNULL(
    CAST(
      `cliente_endereco`.`bairro` AS CHAR charset utf8mb4
    ),
    '0'
  ) AS `bairro`,
  IFNULL(
    CAST(
      `cliente_endereco`.`cidade` AS CHAR charset utf8mb4
    ),
    '0'
  ) AS `cidade`,
  IFNULL(
    CAST(
      `cliente_endereco`.`sigla_uf` AS CHAR charset utf8mb4
    ),
    '0'
  ) AS `uf`,
  IFNULL(
    CAST(
      `cliente_endereco`.`endereco` AS CHAR charset utf8mb4
    ),
    '0'
  ) AS `endereco`,
  IFNULL(
    CAST(
      `cliente_endereco`.`numero` AS CHAR charset utf8mb4
    ),
    '0'
  ) AS `numero`,
  IFNULL(
    CAST(`cliente_endereco`.`cep` AS CHAR charset utf8mb4),
    '0'
  ) AS `cep`,
  IFNULL(
    CAST(
      DATE_FORMAT(`cliente`.`dt_implant`, "%%Y-%%m-%%d %%H:%%i:%%s") AS CHAR charset utf8mb4
    ),
    'null'
  ) AS `dt_cadastro`
FROM
  (
    (
      (
        (
          `cd_cliente` AS `cliente`
          LEFT JOIN `cd_cliente_endereco` AS `cliente_endereco` ON (
            `cliente_endereco`.`cod_cliente` = `cliente`.`cod_cliente`
          )
        )
        LEFT JOIN `cd_cliente_atividade` AS `cliente_atividade` ON (
          `cliente_atividade`.`cod_cliente` = `cliente`.`cod_cliente`
        )
      )
      LEFT JOIN `cd_ramo_atividade` AS `ramo_atividade` ON (
        `cliente_atividade`.`cod_ramo_atividade` = `ramo_atividade`.`cod_ramo_atividade`
      )
    )
  )
WHERE
  (
    `cliente`.`cod_cliente` IN (
      SELECT
        DISTINCTROW `nota_fiscal`.`cod_cliente`
      FROM
        `vd_nota_fiscal` AS `nota_fiscal`
      WHERE (`nota_fiscal`.`dt_emissao` >= SUBDATE(CURDATE(), INTERVAL 2 YEAR))
        AND (`nota_fiscal`.`cod_empresa` IN (1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 15, 16))
        AND (`nota_fiscal`.`situacao` > 79)
        AND (`nota_fiscal`.`situacao` < 86))
 )
GROUP BY `cliente`.`cod_cliente`;