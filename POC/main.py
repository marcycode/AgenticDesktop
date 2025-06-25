from prompt_agent import get_command_steps
from desktop_actions import execute_steps
from speech_input import get_voice_command

def main():
    print("Type your command or say it (press V for voice input):")
    mode = input("Mode [T/V]: ").strip().lower()

    if mode == 'v':
        user_input = get_voice_command()
    else:
        user_input = input(">> ")

    print(f"\n🧠 Interpreting: {user_input}")
    steps = get_command_steps(user_input)
    print(f"\n✅ Steps:\n{steps}")

    execute = input("\nExecute? [Y/N]: ").strip().lower()
    if execute == 'y':
        execute_steps(steps)

if __name__ == "__main__":
    main()
