using Paylocity.Tax.TDV.Common.Infrastructure.Resilience;
using System.Diagnostics.CodeAnalysis;

namespace Paylocity.Distribution.PrintPlatform.WebApi.Infrastructure.AddressApi;

[ExcludeFromCodeCoverage]
public class AddressDependencyResolution
{
  public static void Configure(
    IConfiguration configuration,
    IServiceCollection serviceCollection)
  {
    if (configuration.GetValue<bool>("address_api_use_stub"))
    {
      serviceCollection.AddSingleton<IAddressHttpClient, StubAddressHttpClient>();
      return;
    }

    serviceCollection
      .AddHttpClient<IAddressHttpClient, AddressHttpClient>(client =>
      {
        client.BaseAddress = new Uri(
          configuration["address_api_base_url"]
          ?? throw new InvalidOperationException("address_api_base_url configuration is missing")
        );
      })
      .AddPolicyHandler(HttpResiliencePolicy.DefaultRetryPolicy)
      .AddPolicyHandler(request =>
      {
        return HttpResiliencePolicy.DefaultTimeoutPolicy;
      });
  }
}
