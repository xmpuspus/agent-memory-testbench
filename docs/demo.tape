# Terminal half of the README recording.
#
# docs/record_demo.sh substitutes __VENV_BIN__ and __WORKDIR__ for a throwaway
# virtual environment that holds only the built wheel, then runs vhs on the
# result. The paths never reach a committed file and never reach a visible
# frame: the setup runs inside Hide, and the working directory is a temporary
# one, so no home directory or checkout path appears on screen.

Output "__WORKDIR__/terminal.mp4"

Set FontSize 20
Set Width 960
Set Height 540
Set Padding 20
Set Theme "Atom"
Set Shell zsh

Hide
Type "export PATH=__VENV_BIN__:$PATH && cd __WORKDIR__/stage && unset ANTHROPIC_API_KEY OPENAI_API_KEY && export BROWSER=true && PS1='$ '"
Enter
Sleep 300ms
Type "clear"
Enter
Sleep 200ms
Show

Type "memory-arena demo"
Sleep 600ms
Enter
Sleep 4200ms
