# Turtle Draw

Pipeline de visão computacional que lê uma imagem, extrai seus contornos e controla a tartaruga do **Turtlesim** via ROS 2 para reproduzir o desenho na tela.

## Estrutura do Repositório

```
TurtleDraw/
├── coordenadas.csv              # Coordenadas geradas pelo notebook (entrada do ROS 2)
├── notebooks/
│   ├── dog.jpg                  # Imagem de entrada
│   └── visao-computacional.ipynb # Pipeline completa de visão computacional
└── src/
    └── controle_tartaruga/      # Pacote ROS 2
        ├── controle_tartaruga/
        │   └── desenhador_node.py
        ├── package.xml
        └── setup.py
```

## Pré-requisitos

| Dependência | Versão recomendada |
|---|---|
| Ubuntu | 22.04 (Jammy) |
| ROS 2 | Humble Hawksbill |
| Python | 3.10+ |
| NumPy | qualquer versão recente |
| Matplotlib | qualquer versão recente |
| OpenCV (`cv2`) | qualquer versão recente |
| Jupyter Notebook / JupyterLab | para rodar o notebook |


## Passo 1 - Gerar o arquivo `coordenadas.csv`

Este passo executa a pipeline de visão computacional e gera o CSV com os pontos do contorno mapeados para o espaço do Turtlesim.

```bash
# Acesse a pasta de notebooks
cd TurtleDraw/notebooks

# Abra o Jupyter
jupyter notebook
```

1. Abra o arquivo **`visao-computacional.ipynb`**.
2. Execute todas as células em ordem (`Kernel > Restart & Run All`).
3. Na última célula, **ajuste o caminho de salvamento** do CSV para um caminho válido no seu sistema:

```python
# Altere esta variável na célula de geração do CSV
pasta_projeto = "/caminho/absoluto/para/TurtleDraw"
```

4. Após a execução, o arquivo `coordenadas.csv` será salvo na raiz do projeto.


## Passo 2 - Atualizar o caminho do CSV no nó ROS 2

Abra o arquivo do nó e atualize a variável `caminho_csv` com o caminho absoluto correto para o `coordenadas.csv` gerado no passo anterior:

```bash
# Edite o nó
nano TurtleDraw/src/controle_tartaruga/controle_tartaruga/desenhador_node.py
```

Localize a linha:

```python
caminho_csv = '/mnt/c/Users/Inteli/OneDrive/Área de Trabalho/TurtleDraw/coordenadas.csv'
```

Substitua pelo caminho correto no seu sistema, por exemplo:

```python
caminho_csv = '/home/seu_usuario/TurtleDraw/coordenadas.csv'
```


## Passo 3 - Compilar o pacote ROS 2

```bash
# Acesse a pasta src do workspace
cd TurtleDraw/src

# Compile o pacote
colcon build --packages-select controle_tartaruga

# Faça o source do ambiente gerado
source install/setup.bash
```


## Passo 4 - Iniciar o Turtlesim

Abra um **novo terminal**, carregue o ROS 2 e inicie o simulador:

```bash
# Carregue o ambiente ROS 2
source /opt/ros/humble/setup.bash

# Inicie o Turtlesim
ros2 run turtlesim turtlesim_node
```

## Passo 5 - Executar o nó desenhador

Em outro terminal, dentro da pasta `TurtleDraw/src`:

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 run controle_tartaruga desenhador
```

A tartaruga começará a percorrer o contorno da imagem automaticamente. O progresso é exibido no terminal a cada 100 pontos:

```
[INFO] [desenhador_turtle_node]: 1004 coordenadas carregadas com sucesso.
[INFO] [desenhador_turtle_node]: Ponto 100/1004
[INFO] [desenhador_turtle_node]: Ponto 200/1004
...
[INFO] [desenhador_turtle_node]: Desenho concluído.
```


## Parâmetros Ajustáveis

| Parâmetro | Local | Descrição |
|---|---|---|
| Passo de amostragem | Notebook, célula de CSV | `caminho_final_robo[::25]` — controla a densidade de pontos. Valores entre 15–35 são recomendados. |
| Tolerância de chegada | `desenhador_node.py` | `tolerancia = 0.12` — distância mínima para considerar um ponto atingido. |
| Ganho angular | `desenhador_node.py` | `7.0 * erro_angular` — controla a velocidade de rotação. |
| Velocidade linear máxima | `desenhador_node.py` | `min(1.8 * erro_linear, 1.5)` — limita a velocidade de avanço. |
| Limiar de bordas | Notebook, célula Sobel | Valor aplicado à magnitude do gradiente para binarização. |


## Solução de Problemas

**Tartaruga não se move:** verifique se o Turtlesim está rodando e se o source dos dois ambientes foi feito no mesmo terminal do nó desenhador.

**Erro ao abrir o CSV:** confirme que o caminho em `desenhador_node.py` aponta para o arquivo correto e que ele foi gerado pelo notebook.

**Desenho irreconhecível:** reduza o passo de amostragem (ex: `[::15]`) para aumentar a densidade de pontos e melhorar a fidelidade do contorno.