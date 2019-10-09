#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <unistd.h>

#include "ast.h"
#include "check.h"
#include "main.h"
#include "y.tab.h"

int yyparse();

void				addinstr(char *name, struct ast *expr);
/* Private function prototypes: */
static struct instruction *	getinstr();
static void			usage();

/* Private global variables to keep track of the instruction queue: */
static struct instruction *first = NULL;
static struct instruction *last = NULL;

/*
 * Add an instruction to the instruction queue. If 'name' is null, it is an
 * evaluate instruction; otherwise it is a bind instruction.
 */
void
addinstr(char *name, struct ast *expr)
{
	checktree(expr, false);
	// Make the new instruction:
	struct instruction *new = malloc(sizeof(struct instruction));
	if (name != NULL)
		new->name = strdup(name);
	new->expr = expr;
	new->next = NULL;

	// Push it onto the queue:
	if (first == NULL)
		first = new;
	if (last == NULL)
		last = new;
	else {
		last->next = new;
		last = new;
	}
}

/*
 * Remove and return an instruction from the instruction queue.
 */
static struct instruction *
getinstr()
{
	struct instruction *ret = first;
	first = first->next;
	return (ret);
}

static void
usage(char *program)
{
	printf("usage: %s [-s] [filename]\n", program);
	exit(1);
}

int
main(int argc, char **argv)
{
	int c, fd;
	extern int optind;
	bool simplify_flag = false, debug_flag = false;

	/* Process command line arguments: */
	while ((c = getopt(argc, argv, "sd")) != -1) {
		switch (c) {
		case 's':
			simplify_flag = true;
			break;
		case 'd':
			debug_flag = true;
			break;
		default:
			usage(argv[0]);
		}
	}
	
	/* Open the file if provided (use stdin if not: */
	if (optind == argc) // No extra args, use stdin.
		fd = 0;
	else if (optind == argc - 1) // One extra arg, use as input.
		fd = open(argv[optind], O_RDONLY);
	else
		usage(argv[0]); // Wrong number of arguments.
	if (fd < 0)
		usage(argv[0]); // Invalid filename.
	dup2(fd, 0); // Redirect input from file to stdin.

	// Parse the program using code generated by yacc:
	yyparse();

	initinterp();
	while (first != NULL) {
		execute(getinstr(), simplify_flag, debug_flag);
	}

	return (0);
}
