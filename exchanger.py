from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.types import TxOpts
from spl.token.instructions import get_associated_token_address
from solana.transaction import TransactionInstruction, AccountMeta
import asyncio

# Конфигурация
TESTNET_URL = "https://rpc.ankr.com/solana_devnet"
TOKEN_A_MINT = "So11111111111111111111111111111111111111112"
TOKEN_B_MINT = "BQcdHdAQW1hczDbBi9hiegXAR7A98Q9jx3X3iBBBDiq4"

# Данные пула ликвидности
POOL_PROGRAM_ID = PublicKey("CPMDWBwJDtYax9qW7AyRuVC19Cc4L4Vcy4n2BHAbHkCW")  # Адрес программы пула, например, Raydium
POOL_ACCOUNT = PublicKey("CPMDWBwJDtYax9qW7AyRuVC19Cc4L4Vcy4n2BHAbHkCW")  # Адрес пула ликвидности
POOL_AUTHORITY = PublicKey("441dvocuhsZCrW8zkGGmqYrbd9GWn7Y71YpDDkALTkaz")  # Авторитет пула
TOKEN_A_POOL_ACCOUNT = PublicKey("So11111111111111111111111111111111111111112")  # Аккаунт пула для TOKEN_A
TOKEN_B_POOL_ACCOUNT = PublicKey("6LF1yXthyJE7QjxwKWZv6isRccV76NvRgkwfH3m6YsG4")  # Аккаунт пула для TOKEN_B

async def get_balance(client, pubkey):
    """Получение баланса в SOL."""
    try:
        response = await client.get_balance(pubkey)
        balance = response["result"]["value"] / 1e9  # Перевод из лампортов в SOL
        return balance
    except Exception as e:
        print("Ошибка получения баланса:", e)
        return None

async def get_blockhash(client):
    """Получение актуального блокхеша."""
    try:
        response = await client.get_latest_blockhash()
        return response['result']['value']['blockhash']
    except Exception as e:
        print("Ошибка получения блокхеша:", e)
        return None

def create_transfer_checked_instruction(source, destination, mint, owner, amount, decimals):
    """Создать инструкцию для transfer_checked."""
    return TransactionInstruction(
        program_id=PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"),
        keys=[
            AccountMeta(pubkey=source, is_signer=False, is_writable=True),
            AccountMeta(pubkey=mint, is_signer=False, is_writable=False),
            AccountMeta(pubkey=destination, is_signer=False, is_writable=True),
            AccountMeta(pubkey=owner, is_signer=True, is_writable=False),
        ],
        data=bytes([12]) + amount.to_bytes(8, "little") + decimals.to_bytes(1, "little"),
    )

async def check_account_info(client, account, expected_mint=None):
    """
    Проверяет информацию об аккаунте с использованием getAccountInfo.
    """
    try:
        response = await client.get_account_info(account)
        if response["result"]["value"] is None:
            print(f"Аккаунт {account} не существует.")
            return False

        # Проверка данных аккаунта
        account_data = response["result"]["value"]["data"][0]
        if expected_mint:
            mint = PublicKey(account_data[32:64])  # Поле mint в структуре токенового аккаунта
            if mint != expected_mint:
                print(f"Аккаунт {account} связан с неверным токеном.")
                return False
        print(f"Аккаунт {account} корректен.")
        return True
    except Exception as e:
        print(f"Ошибка проверки аккаунта {account}: {e}")
        return False


async def swap_tokens(client, owner, token_a_source, token_b_destination, amount):
    """
    Обмен токенов A на токены B через пул ликвидности.
    """
    tx = Transaction()
    try:
        # Инструкция перевода токенов A в аккаунт пула
        tx.add(
            create_transfer_checked_instruction(
                source=token_a_source,
                destination=TOKEN_A_POOL_ACCOUNT,
                mint=PublicKey(TOKEN_A_MINT),
                owner=owner.public_key,
                amount=amount,
                decimals=6,
            )
        )
        # Инструкция вызова пула ликвидности для обмена
        tx.add(
            TransactionInstruction(
                keys=[
                    AccountMeta(pubkey=owner.public_key, is_signer=True, is_writable=True),
                    AccountMeta(pubkey=token_a_source, is_signer=False, is_writable=True),
                    AccountMeta(pubkey=TOKEN_A_POOL_ACCOUNT, is_signer=False, is_writable=True),
                    AccountMeta(pubkey=TOKEN_B_POOL_ACCOUNT, is_signer=False, is_writable=True),
                    AccountMeta(pubkey=token_b_destination, is_signer=False, is_writable=True),
                    AccountMeta(pubkey=POOL_ACCOUNT, is_signer=False, is_writable=False),
                    AccountMeta(pubkey=POOL_AUTHORITY, is_signer=False, is_writable=False),
                ],
                program_id=POOL_PROGRAM_ID,
                data=b"",  # Данные инструкции (определяются программой пула)
            )
        )

        # Получение блокхеша и отправка транзакции
        blockhash = await get_blockhash(client)
        if not blockhash:
            print("Не удалось получить блокхеш.")
            return

        tx.fee_payer = owner.public_key
        tx.recent_blockhash = blockhash
        response = await client.send_transaction(tx, owner, opts=TxOpts(skip_preflight=True))
        print("Токены успешно обменяны. Транзакция:", response)
    except Exception as e:
        print("Ошибка обмена токенов:", e)

async def main():
    async with AsyncClient(TESTNET_URL) as client:
        owner = Keypair.from_secret_key(bytes(OWNER_PRIVATE_KEY))
        owner_pubkey = owner.public_key

        # Связанные аккаунты токенов
        token_a_account = get_associated_token_address(owner_pubkey, PublicKey(TOKEN_A_MINT))
        token_b_account = get_associated_token_address(owner_pubkey, PublicKey(TOKEN_B_MINT))

        # Проверка токеновых аккаунтов
        token_a_valid = await check_account_info(client, token_a_account, expected_mint=PublicKey(TOKEN_A_MINT))
        token_b_valid = await check_account_info(client, token_b_account, expected_mint=PublicKey(TOKEN_B_MINT))

        if not (token_a_valid and token_b_valid):
            print("Проверьте связанные токеновые аккаунты. Обмен не может быть выполнен.")


        # Баланс перед транзакцией
        initial_balance = await get_balance(client, owner_pubkey)
        if initial_balance is not None:
            print(f"Баланс перед транзакцией: {initial_balance:.6f} SOL")

        # Выполните обмен токенов
        swap_amount = 5  # Количество токенов A для обмена (в минимальных единицах)
        await swap_tokens(
            client,
            owner,
            token_a_account,
            token_b_account,
            swap_amount
        )

        # Баланс после транзакции
        final_balance = await get_balance(client, owner_pubkey)
        if final_balance is not None:
            print(f"Баланс после транзакции: {final_balance:.6f} SOL")


asyncio.run(main())
