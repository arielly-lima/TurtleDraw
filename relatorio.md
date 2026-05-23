# Relatório Técnico - Turtle Draw

**Disciplina:** Robótica e Visão Computacional  

## Visão Geral

Este projeto implementa uma pipeline completa de visão computacional que lê uma imagem de um cão, extrai seus contornos e traduz as coordenadas resultantes em comandos de movimento para a tartaruga do Turtlesim via ROS 2.<br>
Todo o processamento de imagem por meio de visão computacional foi implementado do zero com **NumPy**, usando **OpenCV** apenas para a leitura inicial da imagem.<br>
Abaixo, estão descritos os processos realizadas em cada etapa do pipeline de visão computacional.<br>

## 1. Pré-processamento

### 1.1 Conversão para Escala de Cinza

A imagem RGB foi convertida para escala de cinza por meio da fórmula de luminância ponderada `Y = 0.299·R + 0.587·G + 0.114·B`, implementada com `np.dot`. Essa ponderação reflete a sensibilidade do olho humano a cada canal de cor e preserva melhor o contraste perceptual do que uma média simples entre os canais — o que é importante para destacar bordas em regiões de baixo contraste cromático.

### 1.2 Suavização Gaussiana

Foi implementada uma convolução 2D manual com um kernel gaussiano e a função foi aplicada **três vezes consecutivas** à imagem em tons de cinza. Cada passagem reduz ruídos de alta frequência e suaviza gradientes; entretanto, uma única aplicação se mostrou insuficiente para eliminar o ruído de textura do pelo do cão. Duas passagens já melhoraram o resultado, mas pequenos artefatos persistiam nas bordas internas. Somente com a terceira aplicação o mapa de bordas ficou limpo o suficiente para gerar um contorno coerente.

**Dificuldade encontrada:** Calibrar o número de passagens exigiu experimentação iterativa. Poucas passagens produziam bordas fragmentadas e ruidosas; passagens demais borravam detalhes estruturais importantes do contorno do animal.

## 2. Detecção de Bordas

### 2.1 Operador de Sobel

A detecção de bordas foi realizada com o operador de Sobel, aplicando convoluções separadas com os kernels 3×3 horizontal (`Sobel_x`) e vertical (`Sobel_y`) sobre a imagem suavizada. A magnitude do gradiente foi calculada como `magnitude = √(Gx² + Gy²)`.

A escolha do Sobel se justifica pela sua robustez a ruídos, usando uma janela 3×3 que combina derivação e suavização, e pela facilidade de controlar a sensibilidade via limiarização.

### 2.2 Limiarização

Após o cálculo da magnitude, um limiar foi aplicado para binarizar o mapa de bordas, retendo apenas os pixels de alta intensidade de gradiente. 

**Dificuldade encontrada:** Encontrar o limiar ideal exigiu múltiplas tentativas. Um limiar baixo capturava bordas de textura do pelo (ruído desnecessário); um limiar alto eliminava partes importantes do contorno externo do cão. O valor final foi ajustado empiricamente para equilibrar completude e limpeza do contorno.


## 3. Planejamento de Caminho

### 3.1 Extração e Ordenação dos Pontos

Os pixels de borda foram extraídos com `np.argwhere` e filtrados para remover uma margem de 10 pixels nas bordas da imagem (artefatos da convolução). Os pontos foram então reordenados usando uma busca greedy de vizinho mais próximo: partindo do primeiro ponto, o algoritmo seleciona sempre o pixel não visitado mais próximo do ponto atual. Essa estratégia minimiza os saltos abruptos no trajeto e resulta em um caminho contínuo que a tartaruga consegue seguir de forma coerente.

**Dificuldade encontrada:** Extrair coordenadas em ordem sequencial foi o maior desafio do processamento. Sem ordenação, a tartaruga pulava aleatoriamente entre regiões distantes da imagem, tornando o desenho irreconhecível. A busca por vizinho mais próximo resolveu o problema, embora para contornos muito densos o custo computacional fosse elevado.

### 3.2 Mapeamento para o Espaço do Turtlesim

As coordenadas de pixel foram mapeadas linearmente para o espaço do simulador (0 a 11 unidades em X e Y), com inversão do eixo vertical — necessária porque o eixo Y da imagem cresce para baixo enquanto no Turtlesim cresce para cima.

### 3.3 Otimização da Densidade de Pontos

Para reduzir o tempo de execução e evitar movimentos excessivamente pequenos, o caminho final foi amostrado com passo 25: `pontos_otimizados = caminho_final_robo[::25]`. Isso reduziu o arquivo CSV de milhares de pontos para aproximadamente 1.000 coordenadas, mantendo a forma geral do contorno reconhecível.

**Dificuldade encontrada:** Valores de passo muito pequenos (< 10) tornavam a execução no Turtlesim extremamente lenta; valores muito grandes (> 40) perdiam detalhes de curvatura. O valor 25 foi o melhor equilíbrio encontrado entre fidelidade visual e tempo de execução.

## 4. Controle ROS 2

### 4.1 Estrutura do Pacote

O pacote `controle_tartaruga` contém o nó `DesenhadorTurtle`, que lê as coordenadas do CSV e publica mensagens `Twist` no tópico `/turtle1/cmd_vel`. A pose atual é obtida via subscriber no tópico `/turtle1/pose`.

### 4.2 Estratégia de Controle

O nó implementa um controlador proporcional de dois estágios a cada iteração do timer (20 ms):

1. **Correção angular prioritária:** se o erro angular for maior que 0,4 rad, a velocidade linear é reduzida a 0,2 m/s para que a tartaruga gire antes de avançar, evitando derrapagens em curvas fechadas.
2. **Avanço proporcional:** quando alinhada, a velocidade linear escala com o erro linear (`min(1.8 · erro, 1.5)`) e o ganho angular é 7,0. A tolerância de chegada ao ponto alvo é de 0,12 unidades.

**Dificuldade encontrada:** Calibrar a velocidade foi o principal desafio no ROS 2. Velocidades lineares altas (> 2,0) faziam a tartaruga ultrapassar pontos consecutivos sem registrá-los, resultando em um desenho incompleto. Velocidades baixas (< 0,5) tornavam o percurso de ~1.000 pontos extremamente lento. O ganho angular alto (7,0) foi necessário para manter a trajetória precisa sem oscilações.

## Conclusão

A pipeline desenvolvida demonstra com sucesso a cadeia completa de visão computacional aplicada à robótica: ``leitura de imagem → grayscale → suavização gaussiana iterativa → detecção de bordas com Sobel → ordenação de contorno → mapeamento de coordenadas → controle proporcional via ROS 2``. As principais dificuldades estiveram na calibração de parâmetros em cada etapa, resolvidas por experimentação sistemática e análise visual dos resultados intermediários.