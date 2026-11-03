from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import uuid

# --- GERENCIADOR DE USUÁRIO ---
class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('O número de telefone deve ser fornecido')
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(phone_number, password, **extra_fields)

# --- MODELO DE USUÁRIO ---
class CustomUser(AbstractBaseUser, PermissionsMixin):
    phone_number = models.CharField(max_length=20, unique=True, verbose_name="Número de Telefone")
    full_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nome Completo")
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    invite_code = models.CharField(max_length=8, unique=True, blank=True, null=True)
    invited_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Convidado por")
    available_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Saldo Disponível")
    subsidy_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Saldo de Subsídios")
    level_active = models.BooleanField(default=False, verbose_name="Nível Ativo")
    roulette_spins = models.IntegerField(default=0, verbose_name="Giros da Roleta")
    
    # NOVOS CAMPOS PARA LOGICA DE ESTAGIÁRIO
    is_free_plan_used = models.BooleanField(default=False, verbose_name="Plano Gratuito Ativado")
    free_days_count = models.IntegerField(default=0, verbose_name="Dias de Estagiário Usados")

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.phone_number

    def save(self, *args, **kwargs):
        if not self.invite_code:
            while True:
                new_invite_code = uuid.uuid4().hex[:8].upper()
                if not CustomUser.objects.filter(invite_code=new_invite_code).exists():
                    self.invite_code = new_invite_code
                    break
        super().save(*args, **kwargs)

# --- CONFIGURAÇÕES E BANCOS ---
class PlatformSettings(models.Model):
    whatsapp_link = models.URLField(verbose_name="Link do WhatsApp")
    history_text = models.TextField(verbose_name="Texto 'Sobre'")
    deposit_instruction = models.TextField(verbose_name="Instrução Depósito")
    withdrawal_instruction = models.TextField(verbose_name="Instrução Saque")

class PlatformBankDetails(models.Model):
    bank_name = models.CharField(max_length=100)
    IBAN = models.CharField(max_length=100)
    account_holder_name = models.CharField(max_length=100)

class BankDetails(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="bank_details")
    bank_name = models.CharField(max_length=100)
    IBAN = models.CharField(max_length=100)
    account_holder_name = models.CharField(max_length=100)

# --- FLUXO FINANCEIRO ---
class Deposit(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    payer_name = models.CharField(max_length=255, blank=True, null=True)
    proof_of_payment = models.ImageField(upload_to='deposit_proofs/')
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Withdrawal(models.Model):
    STATUS_CHOICES = [('Pendente', 'Pendente'), ('Aprovado', 'Aprovado'), ('Recusado', 'Recusado')]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=50)
    payment_details = models.TextField(blank=True, null=True) 
    withdrawal_details = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pendente')
    created_at = models.DateTimeField(auto_now_add=True)

class Level(models.Model):
    name = models.CharField(max_length=50, unique=True)
    deposit_value = models.DecimalField(max_digits=12, decimal_places=2)
    daily_gain = models.DecimalField(max_digits=12, decimal_places=2)
    monthly_gain = models.DecimalField(max_digits=12, decimal_places=2)
    cycle_days = models.IntegerField()
    image = models.ImageField(upload_to='level_images/')
    
    # NOVOS CAMPOS: Definidos no Django para controlar tarefas diárias por nível e valor unitário
    daily_tasks_count = models.IntegerField(default=1, help_text="Número de tarefas que este nível realiza por dia")
    task_value = models.DecimalField(max_digits=12, decimal_places=2, default=450.00, help_text="Valor unitário de cada tarefa (a soma total diária deve bater com o daily_gain)")

    def __str__(self): 
        return self.name

class UserLevel(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    purchase_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.phone_number} - {self.level.name}"

# BANCO DE PERGUNTAS DE FINANÇAS (Dura vários anos com centenas/milhares de questões)
class FinancialQuestion(models.Model):
    categoria = models.CharField(max_length=100, default="Gestão e Investimentos")
    texto = models.TextField(help_text="Enunciado da pergunta de finanças")
    
    # As 4 opções (A, B, C, D)
    opcao_a = models.CharField(max_length=255)
    opcao_b = models.CharField(max_length=255)
    opcao_c = models.CharField(max_length=255)
    opcao_d = models.CharField(max_length=255)
    
    # A resposta correta ('a', 'b', 'c' ou 'd')
    CORRECT_CHOICES = [
        ('a', 'Opção A'),
        ('b', 'Opção B'),
        ('c', 'Opção C'),
        ('d', 'Opção D'),
    ]
    correct_option = models.CharField(max_length=1, choices=CORRECT_CHOICES, default='a')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.categoria}] {self.texto[:50]}..."

# REGISTRO DE TAREFAS REALIZADAS (Com suporte a erros/acertos e ganho garantido por nível)
class Task(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    earnings = models.DecimalField(max_digits=12, decimal_places=2)
    completed_at = models.DateTimeField(auto_now_add=True)
    task_day = models.DateField(default=timezone.now)
    
    # Dados da questão respondida (mesmo errando, o usuário ganha de acordo com o nível)
    question = models.ForeignKey(FinancialQuestion, on_delete=models.SET_NULL, null=True, blank=True)
    user_answer = models.CharField(max_length=1, blank=True, null=True) # 'a', 'b', 'c' ou 'd'
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        status_text = 'Acerto' if self.is_correct else 'Erro - Ganho Creditado'
        return f"Tarefa de {self.user.phone_number} - {self.earnings} KZ ({status_text})"

# CONTABILIZADOR DE ACERTOS E ERROS DO USUÁRIO PARA OS CARDS
class UserTaskProgress(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='task_progress')
    total_correct = models.IntegerField(default=0)
    total_incorrect = models.IntegerField(default=0)

    def __str__(self):
        return f"Progresso de {self.user.phone_number} (Acertos: {self.total_correct} | Erros: {self.total_incorrect})"

# --- SISTEMA DE SORTEIO POR CÓDIGO ---

class PromoCode(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Código do Cupom")
    value = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor do Prêmio (KZ)")
    is_active = models.BooleanField(default=True, verbose_name="Ativo?")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.value} KZ"

    class Meta:
        verbose_name = "Código de Sorteio"
        verbose_name_plural = "Códigos de Sorteio"

class PromoCodeUsage(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="Usuário")
    promo_code = models.ForeignKey(PromoCode, on_delete=models.CASCADE, verbose_name="Código Usado")
    prize_won = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Prêmio Ganho")
    used_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Uso")

    def __str__(self):
        return f"{self.user.phone_number} usou {self.promo_code.code}"

    class Meta:
        verbose_name = "Histórico de Sorteio"
        verbose_name_plural = "Histórico de Sorteios"

class Roulette(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    prize = models.DecimalField(max_digits=12, decimal_places=2)
    spin_date = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True)
    