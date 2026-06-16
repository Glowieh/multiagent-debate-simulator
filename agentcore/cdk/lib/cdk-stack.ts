import { AgentCoreApplication, type AgentCoreProjectSpec } from '@aws/agentcore-cdk';
import { CfnOutput, SecretValue, Stack, type StackProps } from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { Construct } from 'constructs';

export interface AgentCoreStackProps extends StackProps {
  /**
   * The AgentCore project specification containing agents, memories, and credentials.
   */
  spec: AgentCoreProjectSpec;
  /**
   * Optional LangSmith project name injected per deploy target.
   */
  langsmithProject?: string;
}

function toCdkId(name: string): string {
  return name.replace(/_/g, '');
}

/**
 * CDK Stack that deploys AgentCore infrastructure.
 */
export class AgentCoreStack extends Stack {
  /** The AgentCore application containing all agent environments */
  public readonly application: AgentCoreApplication;

  constructor(scope: Construct, id: string, props: AgentCoreStackProps) {
    super(scope, id, props);

    const { spec, langsmithProject } = props;

    this.application = new AgentCoreApplication(this, 'Application', { spec });

    // LangSmith API key via Secrets Manager (injected at deploy; key set by operator post-deploy)
    for (const env of this.application.environments.values()) {
      const envId = toCdkId(env.agent.name);
      const secret = new secretsmanager.Secret(this, `LangSmithSecret${envId}`, {
        secretName: `${spec.name}/${env.agent.name}/langsmith-api-key`,
        secretStringValue: SecretValue.unsafePlainText(JSON.stringify({ api_key: 'REPLACE_ME' })),
        description: `LangSmith API key for ${env.agent.name} tracing`,
      });

      env.runtime.addEnvironmentVariable('LANGSMITH_SECRET_ARN', secret.secretArn);

      if (langsmithProject) {
        env.runtime.addEnvironmentVariable('LANGSMITH_PROJECT', langsmithProject);
      }

      env.runtime.role.addToPrincipalPolicy(
        new iam.PolicyStatement({
          actions: ['secretsmanager:GetSecretValue'],
          resources: [secret.secretArn],
        })
      );

      new CfnOutput(this, `LangSmithSecretArn${envId}`, {
        value: secret.secretArn,
        description: `LangSmith API key secret ARN for ${env.agent.name}`,
      });
    }

    new CfnOutput(this, 'StackNameOutput', {
      description: 'Name of the CloudFormation Stack',
      value: this.stackName,
    });
  }
}
