# ShopMind demo transcripts

## lamp · turn 1

**Shopper:** Quanto custa a luminária Lume?

Luminária Lume (LUME-LAMP) custa R$ 289,00. Há 14 unidades em estoque. Abajur de mesa com braço articulado, luz quente regulável e base de cerâmica fosca. Pensada para leitura e para o trabalho noturno. Na mesma categoria: Carregador Sol, Suporte Atlas.
Fonte: catálogo LUME-LAMP.

_intent `product` · nodes guard_input → classify_intent → retrieve_catalog → check_inventory → recommend → compose_answer → guard_output · tools search_knowledge, check_inventory, recommend_products · sources catalog:LUME-LAMP, catalog:SOL-CHARGER, catalog:ATLAS-STAND_

## order · turn 1

**Shopper:** Cadê o pedido LM-1042?

Pedido LM-1042 de Ana: enviado. Transportadora Lume Express, rastreio LMX-1042-BR. Saiu do centro de distribuição em São Paulo. Itens: Fone Nimbus (1 × R$ 649,00).
Fonte: pedido LM-1042.

_intent `order` · nodes guard_input → classify_intent → lookup_order → compose_answer → guard_output · tools get_order_status · sources order:LM-1042_

## order · turn 2

**Shopper:** Pode repetir o rastreio?

Pedido LM-1042 de Ana: enviado. Transportadora Lume Express, rastreio LMX-1042-BR. Saiu do centro de distribuição em São Paulo. Itens: Fone Nimbus (1 × R$ 649,00).
Fonte: pedido LM-1042.

_intent `order` · nodes guard_input → classify_intent → lookup_order → compose_answer → guard_output · tools get_order_status · sources order:LM-1042_

## shipping · turn 1

**Shopper:** Quanto fica o frete do fone Nimbus para 01001-000?

Frete para 01001-000 (São Paulo): grátis, porque o pedido chega a R$ 299,00 ou mais. Prazo de até 2 dias úteis.
Fonte: política de frete.

_intent `shipping` · nodes guard_input → classify_intent → quote_shipping → compose_answer → guard_output · tools search_knowledge, check_inventory, quote_shipping · sources policy:shipping_

## handoff · turn 1

**Shopper:** Quero falar com uma pessoa

Vou passar você para um atendente humano. Protocolo LM-H-59F3D8. Você pediu para falar com uma pessoa.

_intent `human` · nodes guard_input → classify_intent → handoff → guard_output · tools — · sources —_
