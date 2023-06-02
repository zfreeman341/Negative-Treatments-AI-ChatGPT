Negative Treatments Project

The negativeTreatments program accepts one argument, a "slug" from Casetext.com. ChatGPT surveys the text and, based on criteria in the program, identifies negative treatment of other cases within the passed-in case. It returns these in a structured format, as discussed in more detail below.

To run this program, you will need an OpenAI API key, as laid out in example.env. You likely have one, but just in case I left the link to the OpenAI API page in the example.env file.

To run the program, type:`
  python3 negativeTreatments.py {slug} in the shell.

The result is a list of negatively treated cases. The list includes the case name, the nature of the negative treatment, an explanation for why chatGPT determined that it was a negative treatment, and a citation.

To guide the AI in determining negative treatments, I've created a list of negative treatment indicators using the root forms of relevant words to reduce complexity (i.e. "overrul" instead of "overruling" and "overruled" separately).

For example, the output for the slug littlejohn-v-state-7 will look like:
  Case: State v. Trusty
  Nature: Overruled
  Text:  To the extent that State v. Trusty, 1 Pennewill 319, 40 A. 766 is inconsistent with this holding, we overrule it.
  Explanation: The paragraph mentions that the holding of State v. Trusty is inconsistent with the current holding
  Citation: State v. Trusty, 1 Pennewill 319, 40 A. 766 is inconsistent with this holding, we overrule it.