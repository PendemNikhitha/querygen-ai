terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# Security group allowing SSH, HTTP, and app ports
resource "aws_security_group" "querygen_sg" {
  name        = "querygen-ai-sg"
  description = "Allow SSH, HTTP, and app traffic"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "querygen-ai-sg"
  }
}

# EC2 instance to host the Dockerized application
resource "aws_instance" "querygen_vm" {
  ami                    = "ami-0c02fb55956c7d316" # Ubuntu 22.04 LTS (us-east-1)
  instance_type          = "t3.micro"               # Free-tier eligible
  key_name               = "querygen-ai-key"         # Must exist in AWS account
  vpc_security_group_ids = [aws_security_group.querygen_sg.id]

  tags = {
    Name = "querygen-ai-vm"
  }

  user_data = <<-EOF
              #!/bin/bash
              apt-get update -y
              apt-get install -y docker.io docker-compose
              systemctl start docker
              systemctl enable docker
              EOF
}

output "instance_public_ip" {
  value = aws_instance.querygen_vm.public_ip
}