import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose

# Importação dos serviços do turtlesim
from turtlesim.srv import TeleportAbsolute, SetPen

import math
import csv
import time  # Adicionado para a pequena pausa inicial

class DesenhadorTurtle(Node):

    def __init__(self):
        super().__init__('desenhador_turtle_node')

        # Publisher
        self.publisher_ = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)

        # Subscriber
        self.subscription = self.create_subscription(Pose, '/turtle1/pose', self.pose_callback, 10)

        # Clientes de Serviço para Teleport
        # Pose atual
        self.x_atual = 0.0
        self.y_atual = 0.0
        self.theta_atual = 0.0

        # Caminho
        self.caminho = []
        self.indice_atual = 0
        self.finalizado = False

        # CSV
        caminho_csv = '/mnt/c/Users/Inteli/OneDrive/Área de Trabalho/TurtleDraw/coordenadas.csv'

        # Carrega as coordenadas do CSV
        try:
            with open(caminho_csv, 'r') as file:
                leitor_csv = csv.reader(file)

                for linha in leitor_csv:
                    if len(linha) < 2:
                        continue
                    try:
                        x = float(linha[0])
                        y = float(linha[1])
                        self.caminho.append((x, y))
                    except ValueError:
                        continue

            self.get_logger().info(
                f'{len(self.caminho)} coordenadas carregadas com sucesso.'
            )

        except Exception as e:
            self.get_logger().error(f'Erro ao carregar CSV: {str(e)}')

        # Execução do Drop Inicial Seguro
        req_teleport = TeleportAbsolute.Request()
        req_teleport.x = 10.0
        req_teleport.y = 10.0
        req_teleport.theta = 0.0
 
        # Pequena pausa manual para garantir que o simulador processe o teleport 
        # antes do timer de controle começar a rodar motores
        time.sleep(0.5)

        # Timer inicializado após o setup físico da tartaruga
        self.timer = self.create_timer(0.02, self.control_loop)

    # Callback para atualizar a pose atual da tartaruga
    def pose_callback(self, msg):
        self.x_atual = msg.x
        self.y_atual = msg.y
        self.theta_atual = msg.theta

    # Loop de controle para mover a tartaruga ao longo do caminho
    def control_loop(self):
        if self.finalizado:
            return

        # Verifica se o caminho foi completamente percorrido
        if self.indice_atual >= len(self.caminho):
            msg_parar = Twist()
            self.publisher_.publish(msg_parar)
            self.get_logger().info('Desenho concluído.')
            self.finalizado = True
            return

        x_alvo, y_alvo = self.caminho[self.indice_atual]

        # cálculo do erro linear e angular
        # O erro linear é a distância direta entre a posição atual e o ponto alvo
        dx = x_alvo - self.x_atual
        dy = y_alvo - self.y_atual
        erro_linear = math.sqrt(dx**2 + dy**2)

        # O erro angular é a diferença entre a direção atual da tartaruga e a direção desejada para o ponto alvo
        angulo_desejado = math.atan2(dy, dx)
        erro_angular = angulo_desejado - self.theta_atual

        erro_angular = math.atan2(math.sin(erro_angular), math.cos(erro_angular))

        # Controle de velocidade baseado no erro linear e angular
        msg_vel = Twist()
        tolerancia = 0.12  # Aumentada levemente para evitar órbitas infinitas

        if erro_linear > tolerancia:
            # Se o erro angular for grande, prioriza a correção angular antes de avançar
            if abs(erro_angular) > 0.4:
                msg_vel.linear.x = 0.2  # Praticamente para e gira
            else:
                msg_vel.linear.x = min(1.8 * erro_linear, 1.5)  # Velocidade máxima mais controlada
            
            msg_vel.angular.z = 7.0 * erro_angular  # Resposta angular rápida

        # Se o erro linear estiver dentro da tolerância, considera o ponto alcançado e passa para o próximo
        else:
            self.indice_atual += 1

            if self.indice_atual % 100 == 0:
                self.get_logger().info(f'Ponto {self.indice_atual}/{len(self.caminho)}')

        self.publisher_.publish(msg_vel)

# Função principal para rodar o nó
def main(args=None):
    rclpy.init(args=args)
    node = DesenhadorTurtle()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()