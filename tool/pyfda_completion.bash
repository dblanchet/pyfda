
_pyfda()
{
  local cur=${COMP_WORDS[COMP_CWORD]}
  local prev=${COMP_WORDS[COMP_CWORD - 1]}

  local units_opts="--meters --feet --celsius --fahrenheit"
  local format_opts="--csv --json --prefix --last"

  # First argument: Command or help flag.
  if (($COMP_CWORD == 1)); then
    COMPREPLY=( $(compgen -W "--help upload setup clear convert info" -- $cur) );
    return 0
  fi

  # Next argument depends on chosen command.
  local cmd=${COMP_WORDS[1]}
  case "$cmd" in

    info)
      # No flags/options, just default file completion.
      return 1
      ;;

    convert)
      case "$cur" in
        -*)
          # Leading dash: Many possible flags/options.
          COMPREPLY=( $(compgen -W "$units_opts $format_opts" -- $cur) );
          return 0
          ;;
        *)
          # Default file completion is possible.
          return 1
          ;;
      esac
      ;;

    upload)
      # Only flags/options.
      COMPREPLY=( $(compgen -W "--port $units_opts $format_opts" -- $cur) );
      return 0
      ;;

    setup)
      COMPREPLY=( $(compgen -W "--port --frequency" -- $cur) );
      return 0
      ;;

    clear)
      COMPREPLY=( $(compgen -W "--port" -- $cur) );
      return 0
      ;;

    esac
}

complete -o default -F _pyfda pyfda.py
